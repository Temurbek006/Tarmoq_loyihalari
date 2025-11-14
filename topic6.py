import sys
import subprocess
import platform
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QProgressBar)
from PyQt5.QtCore import QThread, pyqtSignal, Qt

class PingMonitorThread(QThread):
    update_signal = pyqtSignal(str, bool)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()

    def __init__(self, host, count=10):
        super().__init__()
        self.host = host
        self.count = count
        self.is_running = True

    def run(self):
        param = "-n" if platform.system().lower() == "windows" else "-c"
        for i in range(1, self.count + 1):
            if not self.is_running:
                break
            command = ["ping", param, "1", self.host]
            process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, universal_newlines=True)
            success = False
            for line in process.stdout:
                line = line.strip()
                if "time=" in line.lower() or "reply" in line.lower():
                    success = True
            self.update_signal.emit(f"{self.host} - {'Online' if success else 'Offline'}", success)
            progress = int((i / self.count) * 100)
            self.progress_signal.emit(progress)
            self.msleep(1000)  # 1 soniya kutish
        self.finished_signal.emit()

    def stop(self):
        self.is_running = False

class NetworkMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tarmoq Monitoring")
        self.setGeometry(200, 200, 500, 400)
        self.thread = None
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        layout = QVBoxLayout()

        # Host input
        host_layout = QHBoxLayout()
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Masalan: 8.8.8.8 yoki google.com")
        host_layout.addWidget(QLabel("Host:"))
        host_layout.addWidget(self.host_input)
        layout.addLayout(host_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Boshlash")
        self.stop_btn = QPushButton("To‘xtatish")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        # Progress
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Connections
        self.start_btn.clicked.connect(self.start_monitor)
        self.stop_btn.clicked.connect(self.stop_monitor)

        central.setLayout(layout)
        self.setCentralWidget(central)

    def start_monitor(self):
        host = self.host_input.text().strip()
        if not host:
            self.output.append("❌ Host manzilini kiriting!")
            return
        self.output.clear()
        self.progress.setValue(0)
        self.thread = PingMonitorThread(host, count=10)  # 10 ping yuboriladi
        self.thread.update_signal.connect(self.add_output)
        self.thread.progress_signal.connect(self.progress.setValue)
        self.thread.finished_signal.connect(self.monitor_finished)
        self.thread.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_monitor(self):
        if self.thread:
            self.thread.stop()
            self.thread.wait()
            self.thread = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.output.append("🛑 Monitoring to‘xtatildi.")
        self.progress.setValue(0)

    def monitor_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.output.append("✅ Monitoring yakunlandi.")
        self.progress.setValue(100)

    def add_output(self, text, success):
        color = "#00aa00" if success else "#ff0000"
        self.output.append(f"<span style='color:{color}'>{text}</span>")

    def closeEvent(self, event):
        if self.thread:
            self.thread.stop()
            self.thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = NetworkMonitor()
    w.show()
    sys.exit(app.exec_())
