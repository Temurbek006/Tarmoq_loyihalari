# topic7.py
import socket
import threading
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QHBoxLayout, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt

# PORT
PORT = 5050

# Global o'zgaruvchilar
server_socket = None
clients = []
server_running = False
client_socket = None
client_running = False
username = "Foydalanuvchi"
mode = None  # "server" yoki "client"

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# ===================== SERVER QISMI =====================
def handle_client(conn, addr, text_area):
    try:
        name_msg = conn.recv(1024).decode('utf-8')
        if name_msg.startswith("[NEW_USER]"):
            user = name_msg.replace("[NEW_USER]", "").strip()
        else:
            user = str(addr)
    except:
        user = str(addr)

    text_area.append(f"[YANGI] {user} ulandi ({addr[0]})")
    broadcast(f"{user} suhbatga qo'shildi!", text_area)

    while server_running:
        try:
            msg = conn.recv(1024).decode('utf-8')
            if not msg:
                break
            text_area.append(msg)
            broadcast(msg, text_area, exclude=conn)
        except:
            break

    conn.close()
    if conn in clients:
        clients.remove(conn)
    text_area.append(f"[CHIqDI] {user} uzildi")
    broadcast(f"{user} suhbatdan chiqdi!", text_area)

def broadcast(message, text_area, exclude=None):
    dead_clients = []
    for c in clients:
        if c == exclude:
            continue
        try:
            c.sendall(message.encode('utf-8'))
        except:
            dead_clients.append(c)
    for c in dead_clients:
        if c in clients:
            clients.remove(c)

def start_server(text_area):
    global server_socket, server_running
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("0.0.0.0", PORT))
        server_socket.listen(50)
        server_running = True
        text_area.append(f"[SERVER] {get_local_ip()}:{PORT} da ishlayapti")
        while server_running:
            server_socket.settimeout(1)
            try:
                conn, addr = server_socket.accept()
                clients.append(conn)
                thread = threading.Thread(target=handle_client, args=(conn, addr, text_area))
                thread.daemon = True
                thread.start()
            except socket.timeout:
                continue
            except:
                break
    except Exception as e:
        text_area.append(f"[XATO] Server ishga tushmadi: {e}")

def stop_server(text_area):
    global server_running
    server_running = False
    broadcast("[SERVER TO‘XTADI]", text_area)
    for c in clients[:]:
        try:
            c.close()
        except:
            pass
    clients.clear()
    if server_socket:
        try:
            server_socket.close()
        except:
            pass
    text_area.append("[SERVER] To‘xtadi")

# ===================== CLIENT QISMI =====================
def receive_messages(text_area):
    global client_running
    while client_running:
        try:
            msg = client_socket.recv(1024).decode('utf-8')
            if not msg:
                break
            if msg == "[SERVER TO‘XTADI]":
                text_area.append("[SERVER] Server to‘xtadi. Ulanish uzildi.")
                client_running = False
                break
            text_area.append(msg)
        except:
            if client_running:
                text_area.append("[XATO] Ulanish uzildi.")
            break

def connect_to_server(server_ip, username, text_area):
    global client_socket, client_running
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, PORT))
        client_socket.sendall(f"[NEW_USER]{username}".encode('utf-8'))
        text_area.append(f"[ULANDI] {username} → {server_ip}")
        client_running = True
        thread = threading.Thread(target=receive_messages, args=(text_area,))
        thread.daemon = True
        thread.start()
        return True
    except Exception as e:
        text_area.append(f"[XATO] Ulanib bo‘lmadi: {e}")
        return False

def disconnect_client(text_area):
    global client_running, client_socket
    client_running = False
    if client_socket:
        try:
            client_socket.close()
        except:
            pass
        client_socket = None
    text_area.append("[UZILDI] Serverdan uzildi")

# ===================== GUI =====================
class ChatApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LAN Chat - Server & Client")
        self.setStyleSheet("background-color: #1e1e1e; color: white; font-family: Segoe UI;")
        self.resize(500, 600)

        layout = QVBoxLayout()

        # Rejim tanlash
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Rejim:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Server", "Client"])
        self.mode_combo.currentTextChanged.connect(self.switch_mode)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # Server/Client sozlamalari
        self.settings_widget = QWidget()
        self.settings_layout = QVBoxLayout()
        self.settings_widget.setLayout(self.settings_layout)
        layout.addWidget(self.settings_widget)

        # Chat oynasi
        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(True)
        self.chat_box.setStyleSheet("background-color: #2d2d2d; color: #00ff9f; padding: 10px;")
        layout.addWidget(self.chat_box)

        # Xabar yozish
        input_layout = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Xabar yozing...")
        self.msg_input.setStyleSheet("padding: 8px;")
        input_layout.addWidget(self.msg_input)

        self.send_btn = QPushButton("Yuborish")
        self.send_btn.setStyleSheet("background-color: #00aa88; color: white; font-weight: bold; padding: 8px;")
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

        self.setLayout(layout)
        self.switch_mode("Server")  # Dastlabki rejim

    def switch_mode(self, mode_text):
        global mode
        mode = mode_text.lower()
        self.settings_layout.takeAt(0)
        for i in reversed(range(self.settings_layout.count())):
            self.settings_layout.itemAt(i).widget().setParent(None)

        if mode == "server":
            self.setup_server_ui()
        else:
            self.setup_client_ui()

    def setup_server_ui(self):
        widget = QWidget()
        layout = QVBoxLayout()

        ip = get_local_ip()
        layout.addWidget(QLabel(f"Sizning IP: <b>{ip}</b>"))
        layout.addWidget(QLabel(f"Port: <b>{PORT}</b>"))

        btn_layout = QHBoxLayout()
        self.start_server_btn = QPushButton("Serverni Ishga Tushurish")
        self.start_server_btn.setStyleSheet("background-color: #00aa88; color: white; font-weight: bold;")
        self.start_server_btn.clicked.connect(self.run_server)
        btn_layout.addWidget(self.start_server_btn)

        self.stop_server_btn = QPushButton("To‘xtatish")
        self.stop_server_btn.setStyleSheet("background-color: #aa4444; color: white; font-weight: bold;")
        self.stop_server_btn.clicked.connect(self.stop_server_action)
        self.stop_server_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_server_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        self.settings_layout.addWidget(widget)

    def setup_client_ui(self):
        widget = QWidget()
        layout = QVBoxLayout()

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Ism:"))
        self.name_input = QLineEdit()
        self.name_input.setText("Foydalanuvchi")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("Server IP:"))
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Masalan: 192.168.1.100")
        ip_layout.addWidget(self.ip_input)
        layout.addLayout(ip_layout)

        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Ulanish")
        self.connect_btn.setStyleSheet("background-color: #00aa88; color: white; font-weight: bold;")
        self.connect_btn.clicked.connect(self.connect_action)
        btn_layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("Uzish")
        self.disconnect_btn.setStyleSheet("background-color: #aa4444; color: white; font-weight: bold;")
        self.disconnect_btn.clicked.connect(self.disconnect_action)
        self.disconnect_btn.setEnabled(False)
        btn_layout.addWidget(self.disconnect_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        self.settings_layout.addWidget(widget)

    # ===================== SERVER AMALLAR =====================
    def run_server(self):
        thread = threading.Thread(target=start_server, args=(self.chat_box,))
        thread.daemon = True
        thread.start()
        self.start_server_btn.setEnabled(False)
        self.stop_server_btn.setEnabled(True)

    def stop_server_action(self):
        stop_server(self.chat_box)
        self.start_server_btn.setEnabled(True)
        self.stop_server_btn.setEnabled(False)

    # ===================== CLIENT AMALLAR =====================
    def connect_action(self):
        server_ip = self.ip_input.text().strip()
        name = self.name_input.text().strip() or "Anonim"
        if not server_ip:
            QMessageBox.warning(self, "Xato", "Server IP kiriting!")
            return
        if connect_to_server(server_ip, name, self.chat_box):
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.msg_input.setFocus()

    def disconnect_action(self):
        disconnect_client(self.chat_box)
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)

    # ===================== XABAR YUBORISH =====================
    def send_message(self):
        msg = self.msg_input.text().strip()
        if not msg:
            return

        if mode == "server" and server_running:
            full_msg = f"Server: {msg}"
            self.chat_box.append(full_msg)
            broadcast(full_msg, self.chat_box)
        elif mode == "client" and client_running:
            full_msg = f"{self.name_input.text().strip()}: {msg}"
            try:
                client_socket.sendall(full_msg.encode('utf-8'))
            except:
                self.chat_box.append("[XATO] Xabar yuborilmadi")
        else:
            self.chat_box.append("[XATO] Ulanish yo‘q!")

        self.msg_input.clear()

    def closeEvent(self, event):
        if mode == "server":
            stop_server(self.chat_box)
        elif mode == "client":
            disconnect_client(self.chat_box)
        event.accept()

# ===================== ISHGA TUSHIRISH =====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec_())