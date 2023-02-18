from PIL import Image, ImageGrab
from datetime import datetime
import socket
import time
import os
import ctypes
import subprocess
import psutil

HEADER = 64
PORT = 4848
SCREEN_CHECK = (50, 50)
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISSCONECT"
ADDR = (SERVER, PORT)

for i in range(0, 2):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDR)
        connection_error = None
    except Exception as e:
        connection_error = str(e)
    if connection_error:
        print(f"[ERROR] Failed connecting to {SERVER}")
        time.sleep(4)
    else:
        break


def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    print(client.recv(2048).decode(FORMAT))


def get_current_online_status():
    """Can return either "CustomerReady" or "WhiteScreen\""""
    """Checking color of pixels"""

    def getHex(rgb):
        return '%02X%02X%02X' % rgb

    bbox = (SCREEN_CHECK[0], SCREEN_CHECK[1], SCREEN_CHECK[0] + 1, SCREEN_CHECK[1] + 1)
    im = ImageGrab.grab(bbox=bbox)
    rgbim = im.convert('RGB')
    r, g, b = rgbim.getpixel((0, 0))
    #print(f'COLOR: rgb{(r, g, b)} | HEX #{getHex((r, g, b))}')
    if r >= 240 and g >= 240 and b >= 240:
        return 'WhiteScreen'
    else:
        return 'CustomerReady'


def process_exists(process_name):
    call = 'TASKLIST', '/FI', 'imagename eq %s' % process_name
    # use buildin check_output right away
    output = subprocess.check_output(call).decode()
    # check in last line for process name
    last_line = output.strip().split('\r\n')[-1]
    # because Fail message could be translated
    return last_line.lower().startswith(process_name.lower())

def last_boot():
    lib = ctypes.windll.kernel32
    t = lib.GetTickCount64()
    t = int(str(t)[:-3])
    mins, sec = divmod(t, 60)
    hour, mins = divmod(mins, 60)
    days, hour = divmod(hour, 24)
    return days, hour, mins, sec

def get_service(name):
    service = None
    try:
        service = psutil.win_service_get(name)
        service = service.as_dict()
    except Exception as ex:
        # raise psutil.NoSuchProcess if no service with such name exists
        print(str(ex))
    return service


def wait_till_next_minute():
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f'Current time -- {current_time}')
    time_array = []
    for elem in current_time.split(':'):
        time_array.append(int(elem))
    if (60 - time_array[2]) >= 60:
        print('No need to wait, running ...')
    else:
        print(f'Waiting {60 - time_array[2]} more seconds')
        time.sleep(60 - time_array[2])


def get_software_running():
    """Can return info whether MID, winprint or Kiosk soft are running"""
    mid = process_exists('MIDSERV.exe')
    winpint_normal = process_exists('winprint.exe')
    kiosk = process_exists('javaw.exe')
    service = get_service('WinPrint')
    if service:
        # print("Service found: ", service)
        pass
    else:
        # print("Service not found")
        winprint_service = False
    if service and service['status'] == 'running':
        # print("Service is running")
        winprint_service = True
    else:
        winprint_service = False
    return mid, winpint_normal, winprint_service, kiosk

def send_init_message():
    days, hour, mins, sec = last_boot()
    message = f'KIOSK INITIALISATION MESSAGE/LAST BOOT AT-{days}:{hour}:{mins}:{sec}'
    send(message)

#wait_till_next_minute()
send_init_message()
running = True
while running:
    """-------------------------------------------MAIN LOOP-----------------------------------------"""
    mid, winprint_normal, winprint_service, kiosk = False, True, True, True#get_software_running()
    if mid and kiosk and (winprint_service or winprint_normal):
        if winprint_normal and winprint_service:
            print("[ERROR] Both winprint as normal process and winprint as service are running!!!")
            send(f'KIOSK CONNECTION/SENT AT-{datetime.now().strftime("%H:%M:%S")}/BY-{os.getlogin()}/STATUS-2WinPrints')
        else:
            print("[SOFTWARE STATUS] All necessary programs are running...")
            status = get_current_online_status()
            print(f"[KIOSK STATUS] {status}")
            send(f'KIOSK CONNECTION/SENT AT-{datetime.now().strftime("%H:%M:%S")}/BY-{os.getlogin()}/STATUS-{status}')
    else:
        print("[SOFTWARE STATUS] Not all programs are running!!!\n"
              f"\t[MID] {mid}; [WINPRINT_PROCESS] {winprint_normal};\n"
              f"\t[WINPRINT_SERVICE] {winprint_service}; [KIOSK] {kiosk}")
        send(f'KIOSK CONNECTION/SENT AT-{datetime.now().strftime("%H:%M:%S")}/BY-{os.getlogin()}/STATUS-NotAllPrograms')
        days, hour, mins, sec = last_boot()
        if str(days) == '0' and str(hour) == '0' and int(mins)<=2:
            #launch programs
            continue
        else:
            #make some kind of notification that there was a failure launching programs
            continue
    """_____________________________________________________________________________________________"""

    """Code that helps running loop every minute at *:00"""
    time.sleep(2)
    wait_till_next_minute()
    """_________________________________________________"""

    # send result to server
