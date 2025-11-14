# lan_scanner.py
import sys
import subprocess
import platform
import ipaddress
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class PingThread(QThread):
    update_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()

    def __init__(self, ip_list):
        super().__init__()
        self.ip_list = ip_list
        self.is_running = True

    def run(self):
        total = len(self.ip_list)
        for i, ip in enumerate(self.ip_list, 1):
            if not self.is_running:
                break

            alive = self.ping(ip)
            if alive:
                self.update_signal.emit(f"✅ {ip} is active")
            else:
                self.update_signal.emit(f"❌ {ip} is inactive")

            self.progress_signal.emit(int(i / total * 100))
        self.finished_signal.emit()

    def ping(self, ip):
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        try:
            result = subprocess.run(
                ['ping', param, '1', ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return result.returncode == 0
        except Exception:
            return False

    def stop(self):
        self.is_running = False


class LANScanner(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LAN Foydalanuvchilar Scanner")
        self.setGeometry(100, 100, 600, 500)
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: white; font-family: Arial; }
            QLineEdit { background-color: #2d2d2d; border: 1px solid #00ff9f; padding: 5px; }
            QPushButton { background-color: #00aa88; color: white; font-weight: bold; padding: 8px; border: none; }
            QPushButton:hover { background-color: #00ff9f; }
            QTextEdit { background-color: #2d2d2d; border: 1px solid #00ff9f; padding: 5px; }
            QProgressBar { background-color: #2d2d2d; border: 1px solid #00ff9f; text-align: center; }
            QProgressBar::chunk { background-color: #00ff9f; }
        """)

        layout = QVBoxLayout()

        # Subnet input
        subnet_layout = QHBoxLayout()
        subnet_layout.addWidget(QLabel("Subnet kiriting (masalan: 192.168.1.0/24):"))
        self.subnet_input = QLineEdit()
        subnet_layout.addWidget(self.subnet_input)
        layout.addLayout(subnet_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Scan Boshlash")
        self.start_btn.clicked.connect(self.start_scan)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("To‘xtatish")
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        self.clear_btn = QPushButton("Natijalarni Tozalash")
        self.clear_btn.clicked.connect(self.clear_output)
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Output
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        self.setLayout(layout)
        self.thread = None

    def start_scan(self):
        subnet = self.subnet_input.text().strip()
        if not subnet:
            QMessageBox.warning(self, "Xato", "Subnet kiriting!")
            return

        try:
            net = ipaddress.ip_network(subnet, strict=False)
            ip_list = [str(ip) for ip in net.hosts()]
        except ValueError:
            QMessageBox.critical(self, "Xato", "Noto‘g‘ri subnet format!")
            return

        self.output_text.clear()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.thread = PingThread(ip_list)
        self.thread.update_signal.connect(self.add_result)
        self.thread.progress_signal.connect(self.progress.setValue)
        self.thread.finished_signal.connect(self.scan_finished)
        self.thread.start()

    def stop_scan(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.thread.wait()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def add_result(self, text):
        self.output_text.append(text)

    def scan_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.setValue(100)
        self.output_text.append("✅ Scan tugadi!")

    def clear_output(self):
        self.output_text.clear()
        self.progress.setValue(0)
        self.subnet_input.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LANScanner()
    window.show()
    sys.exit(app.exec_())
