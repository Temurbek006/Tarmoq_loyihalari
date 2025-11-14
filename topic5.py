import sys
import subprocess
import platform
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QTabWidget, QSpinBox, QGroupBox,
                             QProgressBar, QFrame, QScrollArea)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QLinearGradient


class PingThread(QThread):
    update_signal = pyqtSignal(str, bool, float)  # text, success, time
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(dict)

    def __init__(self, host, count):
        super().__init__()
        self.host = host
        self.count = count
        self.is_running = True

    def run(self):
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, str(self.count), self.host]

            process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       universal_newlines=True)

            packet_num = 0
            times = []
            success_count = 0

            for line in process.stdout:
                if not self.is_running:
                    process.terminate()
                    break

                # Parse ping results
                if 'time=' in line.lower() or 'vreme=' in line.lower():
                    packet_num += 1
                    time_match = re.search(r'time[=<](\d+\.?\d*)', line.lower())
                    if time_match:
                        time_ms = float(time_match.group(1))
                        times.append(time_ms)
                        success_count += 1
                        self.update_signal.emit(line.strip(), True, time_ms)
                    else:
                        self.update_signal.emit(line.strip(), True, 0)

                    progress = int((packet_num / self.count) * 100)
                    self.progress_signal.emit(progress)
                elif 'reply' in line.lower() or 'javob' in line.lower():
                    self.update_signal.emit(line.strip(), True, 0)
                elif 'timeout' in line.lower() or 'unreachable' in line.lower():
                    packet_num += 1
                    self.update_signal.emit(line.strip(), False, 0)
                    progress = int((packet_num / self.count) * 100)
                    self.progress_signal.emit(progress)

            process.wait()

            # Calculate statistics
            stats = {
                'sent': self.count,
                'received': success_count,
                'lost': self.count - success_count,
                'loss_percent': ((self.count - success_count) / self.count * 100) if self.count > 0 else 0,
                'min': min(times) if times else 0,
                'max': max(times) if times else 0,
                'avg': sum(times) / len(times) if times else 0
            }

            self.finished_signal.emit(stats)

        except Exception as e:
            self.update_signal.emit(f"Xato: {str(e)}", False, 0)
            self.finished_signal.emit({})

    def stop(self):
        self.is_running = False


class TracerouteThread(QThread):
    update_signal = pyqtSignal(str, int, str, float)  # text, hop_num, ip, time
    finished_signal = pyqtSignal(int)

    def __init__(self, host):
        super().__init__()
        self.host = host
        self.is_running = True

    def run(self):
        try:
            if platform.system().lower() == 'windows':
                command = ['tracert', '-d', self.host]
            else:
                command = ['traceroute', '-n', self.host]

            process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       universal_newlines=True)

            hop_count = 0

            for line in process.stdout:
                if not self.is_running:
                    process.terminate()
                    break

                # Parse hop number
                hop_match = re.search(r'^\s*(\d+)', line)
                if hop_match:
                    hop_count += 1
                    hop_num = int(hop_match.group(1))

                    # Parse IP
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    ip = ip_match.group(1) if ip_match else 'N/A'

                    # Parse time
                    time_match = re.search(r'(\d+\.?\d*)\s*ms', line)
                    time_ms = float(time_match.group(1)) if time_match else 0

                    self.update_signal.emit(line.strip(), hop_num, ip, time_ms)

            process.wait()
            self.finished_signal.emit(hop_count)

        except Exception as e:
            self.update_signal.emit(f"Xato: {str(e)}", 0, '', 0)
            self.finished_signal.emit(0)

    def stop(self):
        self.is_running = False


class AnimatedCard(QFrame):
    def __init__(self, title, value, color, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self.color = color

        layout = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setStyleSheet(f'color: {color}; font-size: 14px; font-weight: normal;')

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f'color: {color}; font-size: 32px; font-weight: bold;')

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

        self.setLayout(layout)
        self.setStyleSheet(f"""
            AnimatedCard {{
                background-color: white;
                border-radius: 10px;
                border-left: 5px solid {color};
            }}
        """)

    def update_value(self, value):
        self.value_label.setText(value)


class NetworkDiagnosticTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.ping_results = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('🌐 Tarmoq Diagnostika - Professional')
        self.setGeometry(50, 50, 1200, 800)

        # Global styles
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTabWidget::pane {
                border: none;
                background-color: #f8f9fa;
                border-radius: 15px;
            }
            QTabBar::tab {
                background-color: rgba(255, 255, 255, 0.7);
                color: #333;
                padding: 15px 30px;
                margin-right: 5px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #667eea;
            }
            QTabBar::tab:hover:!selected {
                background-color: rgba(255, 255, 255, 0.9);
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5568d3, stop:1 #6a3f8f);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5bbd, stop:1 #5d357d);
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
            QPushButton#stopButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f093fb, stop:1 #f5576c);
            }
            QPushButton#clearButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4facfe, stop:1 #00f2fe);
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
            }
            QSpinBox {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
            }
            QSpinBox:focus {
                border: 2px solid #667eea;
            }
            QProgressBar {
                border: none;
                border-radius: 10px;
                text-align: center;
                background-color: #e0e0e0;
                height: 20px;
            }
            QProgressBar::chunk {
                border-radius: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: white;
                font-size: 14px;
            }
            QGroupBox::title {
                color: #667eea;
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel('🌐 Tarmoq Diagnostika Dasturi')
        header.setStyleSheet("""
            color: white;
            font-size: 32px;
            font-weight: bold;
            padding: 15px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        """)
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_ping_tab(), '📡 Ping Test')
        self.tabs.addTab(self.create_traceroute_tab(), '🛣️ Traceroute')

        main_layout.addWidget(self.tabs)
        central_widget.setLayout(main_layout)

    def create_ping_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Input section
        input_group = QGroupBox('⚙️ Sozlamalar')
        input_layout = QVBoxLayout()

        host_layout = QHBoxLayout()
        host_label = QLabel('🌍 Host:')
        host_label.setStyleSheet('font-weight: bold; font-size: 13px;')
        self.ping_host_input = QLineEdit()
        self.ping_host_input.setPlaceholderText('google.com, 8.8.8.8, github.com...')
        host_layout.addWidget(host_label, 1)
        host_layout.addWidget(self.ping_host_input, 4)
        input_layout.addLayout(host_layout)

        count_layout = QHBoxLayout()
        count_label = QLabel('📦 Paketlar:')
        count_label.setStyleSheet('font-weight: bold; font-size: 13px;')
        self.ping_count_input = QSpinBox()
        self.ping_count_input.setMinimum(1)
        self.ping_count_input.setMaximum(50)
        self.ping_count_input.setValue(4)
        count_layout.addWidget(count_label, 1)
        count_layout.addWidget(self.ping_count_input, 1)
        count_layout.addStretch(3)
        input_layout.addLayout(count_layout)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Progress bar
        self.ping_progress = QProgressBar()
        self.ping_progress.setVisible(False)
        layout.addWidget(self.ping_progress)

        # Buttons
        button_layout = QHBoxLayout()
        self.ping_start_btn = QPushButton('▶️ Boshlash')
        self.ping_start_btn.clicked.connect(self.start_ping)

        self.ping_stop_btn = QPushButton('⏹️ To\'xtatish')
        self.ping_stop_btn.setObjectName('stopButton')
        self.ping_stop_btn.clicked.connect(self.stop_thread)
        self.ping_stop_btn.setEnabled(False)

        self.ping_clear_btn = QPushButton('🗑️ Tozalash')
        self.ping_clear_btn.setObjectName('clearButton')
        self.ping_clear_btn.clicked.connect(self.clear_ping)

        button_layout.addWidget(self.ping_start_btn)
        button_layout.addWidget(self.ping_stop_btn)
        button_layout.addWidget(self.ping_clear_btn)
        layout.addLayout(button_layout)

        # Statistics cards
        self.stats_widget = QWidget()
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)

        self.card_sent = AnimatedCard('Yuborildi', '0', '#667eea')
        self.card_received = AnimatedCard('Qabul qilindi', '0', '#2ecc71')
        self.card_lost = AnimatedCard('Yo\'qotildi', '0', '#e74c3c')
        self.card_avg = AnimatedCard('O\'rtacha', '0ms', '#f39c12')

        stats_layout.addWidget(self.card_sent)
        stats_layout.addWidget(self.card_received)
        stats_layout.addWidget(self.card_lost)
        stats_layout.addWidget(self.card_avg)

        self.stats_widget.setLayout(stats_layout)
        self.stats_widget.setVisible(False)
        layout.addWidget(self.stats_widget)

        # Results area
        results_group = QGroupBox('📊 Natijalar')
        results_layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { background-color: #1e1e1e; border-radius: 8px; }')

        self.ping_results_widget = QWidget()
        self.ping_results_layout = QVBoxLayout()
        self.ping_results_layout.setSpacing(5)
        self.ping_results_widget.setLayout(self.ping_results_layout)

        scroll.setWidget(self.ping_results_widget)
        results_layout.addWidget(scroll)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        tab.setLayout(layout)
        return tab

    def create_traceroute_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Input section
        input_group = QGroupBox('⚙️ Sozlamalar')
        input_layout = QHBoxLayout()

        host_label = QLabel('🌍 Host:')
        host_label.setStyleSheet('font-weight: bold; font-size: 13px;')
        self.trace_host_input = QLineEdit()
        self.trace_host_input.setPlaceholderText('google.com, 8.8.8.8, github.com...')
        input_layout.addWidget(host_label, 1)
        input_layout.addWidget(self.trace_host_input, 4)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.trace_start_btn = QPushButton('▶️ Boshlash')
        self.trace_start_btn.clicked.connect(self.start_traceroute)

        self.trace_stop_btn = QPushButton('⏹️ To\'xtatish')
        self.trace_stop_btn.setObjectName('stopButton')
        self.trace_stop_btn.clicked.connect(self.stop_thread)
        self.trace_stop_btn.setEnabled(False)

        self.trace_clear_btn = QPushButton('🗑️ Tozalash')
        self.trace_clear_btn.setObjectName('clearButton')
        self.trace_clear_btn.clicked.connect(self.clear_trace)

        button_layout.addWidget(self.trace_start_btn)
        button_layout.addWidget(self.trace_stop_btn)
        button_layout.addWidget(self.trace_clear_btn)
        layout.addLayout(button_layout)

        # Hop counter
        self.trace_hop_label = QLabel('Hops: 0')
        self.trace_hop_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        """)
        self.trace_hop_label.setAlignment(Qt.AlignCenter)
        self.trace_hop_label.setVisible(False)
        layout.addWidget(self.trace_hop_label)

        # Results area
        results_group = QGroupBox('📊 Yo\'nalish')
        results_layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { background-color: #1e1e1e; border-radius: 8px; }')

        self.trace_results_widget = QWidget()
        self.trace_results_layout = QVBoxLayout()
        self.trace_results_layout.setSpacing(5)
        self.trace_results_widget.setLayout(self.trace_results_layout)

        scroll.setWidget(self.trace_results_widget)
        results_layout.addWidget(scroll)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        tab.setLayout(layout)
        return tab

    def add_ping_result(self, text, success, time_ms):
        result_frame = QFrame()
        result_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {'#1b5e20' if success else '#b71c1c'};
                border-radius: 5px;
                padding: 8px;
                margin: 2px;
            }}
        """)

        layout = QHBoxLayout()

        icon = QLabel('✅' if success else '❌')
        icon.setStyleSheet('color: white; font-size: 16px;')

        text_label = QLabel(text[:100])
        text_label.setStyleSheet('color: white; font-size: 12px;')
        text_label.setWordWrap(True)

        if time_ms > 0:
            time_label = QLabel(f'{time_ms:.1f}ms')
            time_label.setStyleSheet('color: #ffeb3b; font-size: 14px; font-weight: bold;')
            layout.addWidget(time_label)

        layout.addWidget(icon)
        layout.addWidget(text_label)
        layout.addStretch()

        result_frame.setLayout(layout)
        self.ping_results_layout.addWidget(result_frame)

    def add_trace_hop(self, text, hop_num, ip, time_ms):
        hop_frame = QFrame()
        hop_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #3498db);
                border-radius: 8px;
                padding: 10px;
                margin: 3px;
            }
        """)

        layout = QHBoxLayout()

        hop_label = QLabel(f'#{hop_num}')
        hop_label.setStyleSheet('color: #f39c12; font-size: 18px; font-weight: bold; min-width: 40px;')

        ip_label = QLabel(ip)
        ip_label.setStyleSheet('color: white; font-size: 14px; font-family: monospace;')

        time_label = QLabel(f'{time_ms:.1f}ms' if time_ms > 0 else '* * *')
        time_label.setStyleSheet('color: #2ecc71; font-size: 14px; font-weight: bold;')

        layout.addWidget(hop_label)
        layout.addWidget(ip_label)
        layout.addStretch()
        layout.addWidget(time_label)

        hop_frame.setLayout(layout)
        self.trace_results_layout.addWidget(hop_frame)

    def start_ping(self):
        host = self.ping_host_input.text().strip()
        if not host:
            self.add_ping_result('❌ Xato: Host manzilini kiriting!', False, 0)
            return

        self.clear_ping()
        count = self.ping_count_input.value()

        self.ping_start_btn.setEnabled(False)
        self.ping_stop_btn.setEnabled(True)
        self.ping_progress.setVisible(True)
        self.ping_progress.setValue(0)
        self.stats_widget.setVisible(True)

        self.thread = PingThread(host, count)
        self.thread.update_signal.connect(self.add_ping_result)
        self.thread.progress_signal.connect(self.ping_progress.setValue)
        self.thread.finished_signal.connect(self.ping_finished)
        self.thread.start()

    def start_traceroute(self):
        host = self.trace_host_input.text().strip()
        if not host:
            self.add_trace_hop('❌ Xato: Host manzilini kiriting!', 0, '', 0)
            return

        self.clear_trace()

        self.trace_start_btn.setEnabled(False)
        self.trace_stop_btn.setEnabled(True)
        self.trace_hop_label.setVisible(True)
        self.trace_hop_label.setText('Hops: 0')

        self.thread = TracerouteThread(host)
        self.thread.update_signal.connect(self.add_trace_hop)
        self.thread.finished_signal.connect(self.trace_finished)
        self.thread.start()

    def ping_finished(self, stats):
        if stats:
            self.card_sent.update_value(str(stats['sent']))
            self.card_received.update_value(str(stats['received']))
            self.card_lost.update_value(f"{stats['lost']} ({stats['loss_percent']:.1f}%)")
            self.card_avg.update_value(f"{stats['avg']:.1f}ms")

        self.ping_start_btn.setEnabled(True)
        self.ping_stop_btn.setEnabled(False)
        self.ping_progress.setVisible(False)

    def trace_finished(self, hop_count):
        self.trace_hop_label.setText(f'Umumiy Hops: {hop_count}')
        self.trace_start_btn.setEnabled(True)
        self.trace_stop_btn.setEnabled(False)

    def clear_ping(self):
        while self.ping_results_layout.count():
            child = self.ping_results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.stats_widget.setVisible(False)

    def clear_trace(self):
        while self.trace_results_layout.count():
            child = self.trace_results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.trace_hop_label.setVisible(False)

    def stop_thread(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.thread.wait()

            self.ping_start_btn.setEnabled(True)
            self.ping_stop_btn.setEnabled(False)
            self.trace_start_btn.setEnabled(True)
            self.trace_stop_btn.setEnabled(False)

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.thread.wait()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NetworkDiagnosticTool()
    window.show()
    sys.exit(app.exec_())