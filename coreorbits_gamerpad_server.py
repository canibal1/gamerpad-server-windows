from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QDialog, QTextEdit, QHBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap, QIcon
import socketio
import sys
from aiohttp import web
import threading
import socket
import io
import logging
import qrcode
import vgamepad as vg
import importlib.metadata as importlib_metadata
from typing import Dict
from pathlib import Path
import re

# SSDP/UPnP support
from ssdpy import SSDPServer

# Gamepad setup
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

# Socket.IO server
sio = socketio.AsyncServer(cors_allowed_origins='*')
sio.always_connect = True

# Helper to get the local IP address
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # connect to DNS server to find out local IP
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()

# Aiohttp server with SSDP registration
def start_server():
    app = web.Application()
    sio.attach(app)

    async def handle(request):
        return web.Response(text="Web server running")

    app.router.add_get('/', handle)

    # SSDP/UPnP advertisement
    ip_address = get_ip()
    port = 8080
    ssdp_server = SSDPServer(
        "GamerPad Service",                      # Unique Service Name
        location=f"http://{ip_address}:{port}/"  # URL clients will fetch
    )
    threading.Thread(
        target=ssdp_server.serve_forever,
        daemon=True
    ).start()
    logger.info(f"SSDP service started: usn=GamerPad Service at http://{ip_address}:{port}/")

    # Start the HTTP + Socket.IO server
    web.run_app(app, port=port)

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()

# Socket.IO events
@sio.event
def connect(sid, environ):
    logger.info(f"Client {sid} connected.")
    gamepad[sid] = vg.VX360Gamepad()

@sio.event
def disconnect(sid):
    logger.info(f"Client {sid} disconnected.")
    gamepad.pop(sid, None)

@sio.on('left_joystick')
def left_joystick(sid, data):
    gamepad[sid].left_joystick_float(data['x'], data['y'])
    gamepad[sid].update()

@sio.on('right_joystick')
def right_joystick(sid, data):
    gamepad[sid].right_joystick_float(data['x'], data['y'])
    gamepad[sid].update()

@sio.on('left_trigger')
def left_trigger(sid, data):
    gamepad[sid].left_trigger_float(data['value'])
    gamepad[sid].update()

@sio.on('right_trigger')
def right_trigger(sid, data):
    gamepad[sid].right_trigger_float(data['value'])
    gamepad[sid].update()

@sio.on('press_button')
def press_button(sid, data):
    print(data)
    btn = gameControls.get(data['id'])
    if btn:
        gamepad[sid].press_button(btn)
        gamepad[sid].update()

@sio.on('release_button')
def release_button(sid, data):
    btn = gameControls.get(data['id'])
    if btn:
        gamepad[sid].release_button(btn)
        gamepad[sid].update()

@sio.on('vibrate')
def vibrate(sid, data):
    gamepad[sid].set_vibration(data.get('large_motor', 0), data.get('small_motor', 0))
    gamepad[sid].update()

@sio.on('cancel_vibration')
def cancel_vibration(sid):
    gamepad[sid].set_vibration(0, 0)
    gamepad[sid].update()

@sio.on('dpad')
def dpad(sid, data):
    mapping = {
        'up': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
        'down': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
        'left': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
        'right': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    }
    btn = mapping.get(data.get('direction'))
    if btn:
        gamepad[sid].press_button(btn)
        gamepad[sid].update()

# QR Code generator
def generate_qr_code():
    ip = get_ip()
    qr = qrcode.make(f'http://{ip}:8080')
    # you can adjust size if needed
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    return buf

# PySide6 GUI
class QRCodeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("GamerPad - CoreOrbits©")
        layout = QVBoxLayout()

        pixmap = QPixmap()
        pixmap.loadFromData(generate_qr_code().getvalue())
        qr_label = QLabel()
        qr_label.setPixmap(pixmap)
        layout.addWidget(qr_label, alignment=Qt.AlignCenter)
        layout.addStretch()

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        self.clients_label = QLabel("Connected clients: 0")
        bottom_layout.addWidget(self.clients_label)

        btn = QPushButton("Licenses")
        btn.setFixedWidth(pixmap.width() // 4)
        bottom_layout.addWidget(btn)
        btn.clicked.connect(self.show_licenses)

        layout.addLayout(bottom_layout)
        self.setLayout(layout)
        self.resize(400, 400)

        timer = QTimer(self)
        timer.timeout.connect(self.update_clients_label)
        timer.start(1000)

    def update_clients_label(self):
        count = len(gamepad)
        self.clients_label.setText(f"Connected clients: {count}")

    def show_licenses(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Licenses & Details")
        dlg_layout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setReadOnly(True)
        try:
            base_path = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
            license_file = base_path / 'licences.txt'
            # Try UTF-8 first, then fall back to Windows-1252 if it fails
            try:
                content = license_file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Fallback to CP1252 for non-UTF8 characters
                content = license_file.read_text(encoding="cp1252")
        except Exception as e:
            content = f"Could not load licenses.txt:\n{e}"
        text.setPlainText(content)
        dlg_layout.addWidget(text)
        dialog.resize(800, 600)
        dialog.exec_()


if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('app_icon.ico')) 

    win = QRCodeApp()
    win.show()
    sys.exit(app.exec_())
