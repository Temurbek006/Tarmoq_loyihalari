# http_analyzer_stdlib.py
import sys
import http.client
import urllib.parse
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt
import time

class HTTPAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HTTP So‘rov Tahlilchisi")
        self.setGeometry(100, 100, 600, 500)
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: white; font-family: Arial; }
            QLineEdit { background-color: #2d2d2d; border: 1px solid #00ff9f; padding: 5px; }
            QPushButton { background-color: #00aa88; color: white; font-weight: bold; padding: 8px; border: none; }
            QPushButton:hover { background-color: #00ff9f; }
            QTextEdit { background-color: #2d2d2d; border: 1px solid #00ff9f; padding: 5px; }
            QLabel { color: #00ff9f; }
        """)

        layout = QVBoxLayout()

        # URL kiritish
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL kiriting (masalan: https://example.com):"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://httpbin.org/get")
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # Tugmalar
        btn_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("Tahlil qilish")
        self.analyze_btn.clicked.connect(self.analyze_request)
        btn_layout.addWidget(self.analyze_btn)

        self.clear_btn = QPushButton("Tozalash")
        self.clear_btn.clicked.connect(self.clear_output)
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)

        # Natijalar oynasi
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        self.setLayout(layout)

    def analyze_request(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Xato", "URL kiriting!")
            return

        try:
            parsed_url = urllib.parse.urlparse(url)
            scheme = parsed_url.scheme
            host = parsed_url.hostname
            path = parsed_url.path if parsed_url.path else "/"
            port = parsed_url.port
            if not port:
                port = 443 if scheme == "https" else 80

            start_time = time.time()
            if scheme == "https":
                conn = http.client.HTTPSConnection(host, port, timeout=10)
            else:
                conn = http.client.HTTPConnection(host, port, timeout=10)

            conn.request("GET", path)
            response = conn.getresponse()
            elapsed_time = time.time() - start_time
            body = response.read().decode('utf-8', errors='replace')

            output = f"=== HTTP SO'ROV TAHLILI ===\n\n"
            output += f"URL: {url}\n\n"

            # Request ma'lumotlari
            output += "=== SO'ROV (REQUEST) ===\n"
            output += f"Method: GET\n"
            output += f"Host: {host}\n"
            output += f"Path: {path}\n\n"

            # Response ma'lumotlari
            output += "=== JAVOB (RESPONSE) ===\n"
            output += f"Kod: {response.status} ({self.get_status_description(response.status)})\n"
            headers = {k:v for k,v in response.getheaders()}
            output += f"Headers: {headers}\n"
            output += f"Body: {body[:1000]}{'...' if len(body) > 1000 else ''}\n\n"

            output += "=== TAHLIL NATIJASI ===\n"
            output += f"- So'rov muvaffaqiyatli: {'Ha' if 200 <= response.status < 400 else 'Yo‘q'}\n"
            output += f"- Vaqt: {elapsed_time:.2f} soniya\n"
            output += f"- Hajm: {len(body.encode('utf-8'))} bayt\n"

            self.output_text.setText(output)

        except Exception as e:
            error_msg = f"Xato: {str(e)}\n\nMaslahat: URL to'g'ri ekanligini tekshiring yoki tarmoqni sinab ko'ring."
            self.output_text.setText(error_msg)
            QMessageBox.critical(self, "Xato", error_msg)

    def get_status_description(self, code):
        descriptions = {
            200: "OK - Muvaffaqiyatli",
            201: "Created - Yaratildi",
            400: "Bad Request - Noto'g'ri so'rov",
            401: "Unauthorized - Ruxsatsiz",
            403: "Forbidden - Taqiqlangan",
            404: "Not Found - Topilmadi",
            500: "Internal Server Error - Server xatosi"
        }
        return descriptions.get(code, "Noma'lum")

    def clear_output(self):
        self.output_text.clear()
        self.url_input.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HTTPAnalyzer()
    window.show()
    sys.exit(app.exec_())
