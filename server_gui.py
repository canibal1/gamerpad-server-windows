import socketio
from aiohttp import web
import vgamepad as vg
import asyncio
import threading
import tkinter as tk
from tkinter import messagebox

# SocketIO setup
sio = socketio.AsyncServer(cors_allowed_origins='*')

# Globals
gamepad = {}
gameControls = {
    'A': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    'B': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    'Y': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
}
vibrating = False
connected_clients = 0
server_running = False
server_thread = None

# Callback for gamepad vibration
def my_callback(client, target, large_motor, small_motor, led_number, user_data):
    global vibrating
    if large_motor > 0 or small_motor > 0:
        if not vibrating:
            asyncio.run(emitVibrate())
            vibrating = True
    else:
        asyncio.run(cancelVibrate())
        vibrating = False

# SocketIO handlers
async def emitVibrate():
    await sio.emit('vibrate')

async def cancelVibrate():
    await sio.emit('cancel-vibrate')

@sio.event
def connect(sid, environ):
    global connected_clients
    gamepad[sid] = vg.VX360Gamepad()
    connected_clients += 1
    update_status()
    print('connect ', sid)

@sio.event
def disconnect(sid):
    global connected_clients
    if sid in gamepad:
        gamepad[sid].__del__()
        del gamepad[sid]
    connected_clients -= 1
    update_status()
    print('disconnect ', sid)

@sio.on('steer')
def steer(sid, data):
    gamepad[sid].left_joystick(x_value=data['x'], y_value=0)
    gamepad[sid].update()

@sio.on('press-accelerate')
def press_accelerate(sid, data):
    gamepad[sid].right_trigger_float(1)
    gamepad[sid].update()

@sio.on('release-accelerate')
def release_accelerate(sid, data):
    gamepad[sid].right_trigger_float(0)
    gamepad[sid].update()

@sio.on('press-brake')
def press_brake(sid, data):
    gamepad[sid].left_trigger_float(1)
    gamepad[sid].update()

@sio.on('release-brake')
def release_brake(sid, data):
    gamepad[sid].left_trigger_float(0)
    gamepad[sid].update()

@sio.on('press')
def press_button(sid, data):
    gamepad[sid].press_button(gameControls[data['id']])
    gamepad[sid].update()

@sio.on('release')
def release_button(sid, data):
    gamepad[sid].release_button(gameControls[data['id']])
    gamepad[sid].update()

# AIOHTTP setup
app = web.Application()
sio.attach(app)

# GUI setup
def start_server():
    global server_running, server_thread
    if not server_running:
        server_running = True
        server_thread = threading.Thread(target=lambda: asyncio.run(web.run_app(app)), daemon=True)
        server_thread.start()
        status_label.config(text="Bağlandı", fg="green")


def stop_server():
    global server_running, server_thread
    if server_running:
        server_running = False
        # Not a perfect solution: aiohttp does not provide direct API to stop the server gracefully
        # Here we just inform the user and rely on GUI closure to stop the background thread
        status_label.config(text="Bağlantı Yok", fg="red")


def update_status():
    connected_label.config(text=f"Bağlı Cihaz Sayısı: {connected_clients}")


def close_app():
    if messagebox.askokcancel("Çıkış", "Uygulamadan çıkmak istediğinize emin misiniz?"):
        stop_server()
        root.destroy()

# Create the main tkinter window
root = tk.Tk()
root.title("Gamepad Kontrol Paneli")
root.geometry("400x250")

# Add GUI elements
connect_button = tk.Button(root, text="Bağlan", command=start_server, bg="blue", fg="white")
connect_button.pack(pady=10)

disconnect_button = tk.Button(root, text="Bağlantıyı Kes", command=stop_server, bg="orange", fg="white")
disconnect_button.pack(pady=10)

status_label = tk.Label(root, text="Bağlantı Yok", fg="red")
status_label.pack(pady=10)

connected_label = tk.Label(root, text="Bağlı Cihaz Sayısı: 0")
connected_label.pack(pady=10)

exit_button = tk.Button(root, text="Çıkış", command=close_app, bg="red", fg="white")
exit_button.pack(pady=10)

# Run the GUI loop
root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()
