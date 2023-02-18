from datetime import datetime
import socket
import threading

HEADER = 64
PORT = 4848
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISSCONECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def msg_as_dict(msg):
    msg = msg.split('/')
    kiosk_log = {
        'Time': msg[1].split('-')[1],
        'From': msg[2].split('-')[1],
        'Status': msg[3].split('-')[1]
    }
    return kiosk_log

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.\n")
    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                connected = False
            cur_time = datetime.now().strftime('%H:%M:%S')
            if msg.find('KIOSK CONNECTION')!=-1 and msg.find('SENT AT')!=-1 and msg.find('STATUS')!=-1:
                print(f'[KIOSK STATUS REPORT] from {addr[0]}')# {msg}')
                kiosk_log = msg_as_dict(msg)
                print(f"\t[TIME] {kiosk_log['Time']}; [USER] {kiosk_log['From']};\n"
                      f"\t[STATUS] {kiosk_log['Status']}")
            if msg.find('KIOSK INITIALISATION MESSAGE')!=-1 and msg.find('LAST BOOT AT')!=-1:
                print(f'[INIT MESSAGE] from {addr[0]}')# {msg}')
            else:
                print(f"[{addr}] {msg}")

            conn.send(f"Server received message at: {cur_time}".encode(FORMAT))


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


print("[STARTING] server is starting ...")
start()
