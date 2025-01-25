from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
import socketio
import sys
from aiohttp import web
import threading
import socket
import tkinter as tk
from PIL import Image, ImageTk
import io
import logging
import qrcode
import vgamepad as vg
from aiohttp import web
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QThread
from PIL import Image
from typing import Dict

gamepad: Dict[str, vg.VX360Gamepad] = {}
gameControls = {
    'A': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    'B': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    'X': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    'Y': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    'UP': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    'DOWN': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    'LEFT': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    'RIGHT': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    'START': vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    'BACK': vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    'LS_CLICK': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    'RS_CLICK': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    'LB': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    'RB': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    'GUIDE': vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
}
sio = socketio.AsyncServer(cors_allowed_origins='*')
sio.always_connect=True

# Aiohttp server
async def handle(request):
    return web.Response(text="Web sunucu çalışıyor!")

def start_server():
    app = web.Application()
    sio.attach(app)
    app.router.add_get('/', handle)
    web.run_app(app, port=8080)

sio.always_connect=True
# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()


# Event for new client connections
@sio.event
def connect(sid, environ):
    logger.info(f"Client {sid} connected.")
    # Initialize the gamepad state for the new client
    gamepad[sid] = vg.VX360Gamepad()

# Event for client disconnections
@sio.event
def disconnect(sid):
    logger.info(f"Client {sid} disconnected.")
    # Perform any necessary cleanup or shutdown
    if sid in gamepad:
        del gamepad[sid]  # Remove gamepad reference for the disconnected client

# Gamepad input handlers

@sio.on('left_joystick')
def left_joystick(sid, data):
    logger.info(f"Received left joystick data from {sid}: {data}")
    gamepad[sid].left_joystick_float(data['x'], data['y'])
    gamepad[sid].update()

@sio.on('right_joystick')
def right_joystick(sid, data):
    logger.info(f"Received right joystick data from {sid}: {data}")
    gamepad[sid].right_joystick_float(data['x'], data['y'])
    gamepad[sid].update()

@sio.on('left_trigger')
def left_trigger(sid, data):
    logger.info(f"Received left trigger data from {sid}: {data}")
    gamepad[sid].left_trigger_float(data['value'])
    gamepad[sid].update()

@sio.on('right_trigger')
def right_trigger(sid, data):
    logger.info(f"Received right trigger data from {sid}: {data}")
    gamepad[sid].right_trigger_float(data['value'])
    gamepad[sid].update()

@sio.on('press_button')
def press_button(sid, data):

    button = gameControls.get(data['id'])
    print(data)
    if button:
        logger.info(f"Received button press from {sid}: {data['id']}")
        gamepad[sid].press_button(button)
        gamepad[sid].update()

@sio.on('release_button')
def release_button(sid, data):
    button = gameControls.get(data['id'])
    if button:
        logger.info(f"Received button release from {sid}: {data['id']}")
        gamepad[sid].release_button(button)
        gamepad[sid].update()

@sio.on('left_thumb_click')
def left_thumb_click(sid):
    logger.info(f"Received left thumb click from {sid}")
    gamepad[sid].press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)
    gamepad[sid].update()

@sio.on('right_thumb_click')
def right_thumb_click(sid):
    logger.info(f"Received right thumb click from {sid}")
    gamepad[sid].press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    gamepad[sid].update()

@sio.on('vibrate')
def vibrate(sid, data):
    logger.info(f"Received vibration data from {sid}: {data}")
    large_motor = data.get('large_motor', 0)
    small_motor = data.get('small_motor', 0)
    gamepad[sid].set_vibration(large_motor, small_motor)
    gamepad[sid].update()

@sio.on('cancel_vibration')
def cancel_vibration(sid):
    logger.info(f"Cancel vibration from {sid}")
    gamepad[sid].set_vibration(0, 0)
    gamepad[sid].update()

@sio.on('dpad')
def dpad(sid, data):
    direction = data.get('direction')
    logger.info(f"Received dpad input from {sid}: {direction}")
    if direction == 'up':
        gamepad[sid].press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
    elif direction == 'down':
        gamepad[sid].press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
    elif direction == 'left':
        gamepad[sid].press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
    elif direction == 'right':
        gamepad[sid].press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
    gamepad[sid].update()

# PyQt GUI
def start_gui():
    app = QApplication(sys.argv)
    window = QRCodeApp()
    layout = QVBoxLayout()
    label = QLabel("Bu bir GUI uygulamasıdır.")
    layout.addWidget(label)
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec_())


# QR code generation function
def generate_qr_code():
    # Get local machine's IPv4 address
    ip_address = socket.gethostbyname(socket.gethostname())
    
    # Generate QR code
    qr = qrcode.make(f'http://{ip_address}:8080')  # Assuming server runs on port 8080
    print( "ip_address" +ip_address)
    # Convert QR code to an image format that PyQt5 can use
    img_byte_array = io.BytesIO()
    qr.save(img_byte_array, format="PNG")
    img_byte_array.seek(0)
    return img_byte_array

# PyQt5 GUI class
class QRCodeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Set up layout
        self.setWindowTitle("QR Code")
        layout = QVBoxLayout()

        # Generate QR code and display it
        img_byte_array = generate_qr_code()
        pixmap = QPixmap()
        pixmap.loadFromData(img_byte_array.getvalue())

        label = QLabel()
        label.setPixmap(pixmap)
        layout.addWidget(label)

        self.setLayout(layout)
        self.resize(300, 300)

# Thread kullanarak GUI ve sunucuyu aynı anda çalıştırma
if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    start_gui()
