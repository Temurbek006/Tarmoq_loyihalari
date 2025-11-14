from flask import Flask, render_template_string, request, redirect, jsonify
import subprocess
import os
from threading import Lock
import requests

app = Flask(__name__)

# Xotirada mavzular ro'yxati (20 ta)
topics = {
    1: {"title": "IP manzillarni avtomatik skanerlovchi va faol hostlarni ko'rsatuvchi ilova", "file": "topic2.py"},
    2: {"title": "Ping va traceroute buyruqlarini grafik interfeysda bajaruvchi dastur", "file": "topic5.py"},
    3: {"title": "Tarmoqda foydalanuvchi ulanish holatini kuzatuvchi monitoring tizimi", "file": "topic6.py"},
    4: {"title": "Lokal chat dasturi (LAN Messenger) – IP orqali xabar almashish", "file": "topic7.py"},
    5: {"title": "Wi-Fi tarmoqlarini aniqlovchi va signal kuchini o'lchovchi dastur", "file": "topic8.py"},
    6: {"title": "HTTP so'rovlarini log qiluvchi va statistik chiqaruvchi dastur", "file": "topic12.py"},
}


# Ishga tushirilgan jarayonlar (faqat bitta run uchun)
running_processes = {}
process_lock = Lock()

# Frontend HTML
FRONTEND_HTML = '''<!DOCTYPE html>
<html lang="uz">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>217-guruh — Tarmoq loyihalari</title>
  <style>
    :root {
      --primary: #667eea;
      --secondary: #764ba2;
      --bg: #f5f7fa;
      --card: #ffffff;
      --text: #2d3748;
      --muted: #718096;
      --border: #e2e8f0;
      --shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
      --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
    }
    .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
    header {
      background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
      padding: 30px;
      border-radius: 16px;
      margin-bottom: 30px;
      box-shadow: var(--shadow-lg);
      text-align: center;
    }
    h1 { color: white; font-size: 28px; font-weight: 700; }
    .main-grid { display: grid; grid-template-columns: 280px 1fr; gap: 20px; align-items: start; }
    .sidebar {
      background: var(--card);
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--shadow);
      position: sticky;
      top: 20px;
    }
    .menu-btn {
      width: 100%;
      padding: 14px 20px;
      background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
      color: white;
      border: none;
      border-radius: 10px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: 0.3s;
      box-shadow: var(--shadow);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .menu-btn:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
    .menu-btn::after { content: '▼'; font-size: 12px; transition: 0.3s; }
    .menu-btn.active::after { transform: rotate(180deg); }
    .topics-list {
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.4s ease;
      margin-top: 15px;
    }
    .topics-list.open {
      max-height: 600px;
      overflow-y: auto;
      padding-right: 5px;
    }
    .topics-list::-webkit-scrollbar { width: 6px; }
    .topics-list::-webkit-scrollbar-track { background: var(--bg); border-radius: 10px; }
    .topics-list::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }
    .topic-item {
      padding: 12px 15px;
      margin: 8px 0;
      background: var(--bg);
      border: 2px solid var(--border);
      border-radius: 8px;
      cursor: pointer;

      transition: 0.2s;
      font-size: 14px;
      line-height: 1.5;
    }
    .topic-item:hover {
      background: white;
      border-color: var(--primary);
      transform: translateX(5px);
      box-shadow: var(--shadow);
    }
    .topic-item.active {
      background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
      color: white;
      border-color: transparent;
    }
    .viewer {
      background: var(--card);
      border-radius: 12px;
      padding: 25px;
      box-shadow: var(--shadow);
      min-height: 600px;
    }
    .viewer-header {
      margin-bottom: 20px;
      padding-bottom: 15px;
      border-bottom: 2px solid var(--border);
    }
    .viewer-title { font-size: 20px; font-weight: 700; color: var(--text); margin-bottom: 5px; }
    .viewer-subtitle { font-size: 14px; color: var(--muted); }
    .run-btn {
      width: 100%;
      padding: 15px;
      background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
      color: white;
      border: none;
      border-radius: 10px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      margin-top: 20px;
      transition: 0.3s;
    }
    .run-btn:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
    .run-btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .status { padding: 15px; background: #f0f9ff; border-left: 4px solid #0ea5e9; border-radius: 8px; margin-top: 15px; }
    @media(max-width: 968px) {
      .main-grid { grid-template-columns: 1fr; }
      .sidebar { position: relative; top: 0; }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>217-guruh — Tarmoq loyihalari</h1>
    </header>
    <div class="main-grid">
      <aside class="sidebar">
        <button class="menu-btn" id="menuBtn">217-guruh</button>
        <div class="topics-list" id="topicsList">
          {% for id, topic in topics.items() %}
          <div class="topic-item" data-id="{{ id }}">{{ id }}. {{ topic.title }}</div>
          {% endfor %}
        </div>
      </aside>
      <main class="viewer">
        <div class="viewer-header">
          <div class="viewer-title" id="viewerTitle">Mavzu tanlang</div>
          <div class="viewer-subtitle" id="viewerSubtitle">Chap tarafdan mavzuni tanlang</div>
        </div>
        <div id="content">
          <p style="text-align: center; color: var(--muted); padding: 50px 0;">📂 Mavzu tanlanmagan</p>
        </div>
      </main>
    </div>
  </div>
  <script>
    const menuBtn = document.getElementById('menuBtn');
    const topicsList = document.getElementById('topicsList');
    const topicItems = document.querySelectorAll('.topic-item');
    const content = document.getElementById('content');
    const viewerTitle = document.getElementById('viewerTitle');
    const viewerSubtitle = document.getElementById('viewerSubtitle');
    let selectedTopic = null;

    menuBtn.addEventListener('click', () => {
      menuBtn.classList.toggle('active');
      topicsList.classList.toggle('open');
    });

    topicItems.forEach(item => {
      item.addEventListener('click', function() {
        selectedTopic = this.dataset.id;
        const title = this.textContent.trim();

        topicItems.forEach(i => i.classList.remove('active'));
        this.classList.add('active');

        viewerTitle.textContent = title;
        viewerSubtitle.textContent = 'Dasturni ishga tushirish uchun tugmani bosing';

        content.innerHTML = `
          <button class="run-btn" onclick="runTopic(${selectedTopic})">▶️ Dasturni ishga tushirish</button>
          <div id="status"></div>
        `;
      });
    });

    async function runTopic(id) {
      const statusDiv = document.getElementById('status');
      statusDiv.innerHTML = '<div class="status">⏳ Dastur ishga tushirilmoqda...</div>';

      try {
        const response = await fetch('/run/' + id, { method: 'POST' });
        const data = await response.json();


        if (data.success) {
          statusDiv.innerHTML = '<div class="status">✅ ' + data.message + '</div>';
        } else {
          statusDiv.innerHTML = '<div class="status" style="background: #fee; border-color: #f00;">❌ ' + data.message + '</div>';
        }
      } catch (error) {
        statusDiv.innerHTML = '<div class="status" style="background: #fee; border-color: #f00;">❌ Xatolik yuz berdi</div>';
      }
    }
  </script>
</body>
</html>'''

# Admin panel HTML
ADMIN_HTML = '''<!DOCTYPE html>
<html lang="uz">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Admin Panel</title>
  <style>
    :root { --primary: #667eea; --secondary: #764ba2; --bg: #f5f7fa; --card: #ffffff; }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Arial, sans-serif; background: var(--bg); padding: 20px; }
    .container { max-width: 1000px; margin: 0 auto; }
    header {
      background: linear-gradient(135deg, var(--primary), var(--secondary));
      color: white;
      padding: 30px;
      border-radius: 12px;
      margin-bottom: 30px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    h1 { font-size: 28px; }
    .back-link { background: white; color: var(--primary); padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 600; }
    .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .form-group { margin-bottom: 20px; }
    label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
    input, select { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
    input:focus { border-color: var(--primary); outline: none; }
    .btn {
      padding: 12px 24px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 600;
      font-size: 14px;
      transition: 0.3s;
    }
    .btn-primary { background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; }
    .btn-danger { background: #f56565; color: white; }
    .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 15px; text-align: left; border-bottom: 1px solid #e0e0e0; }
    th { background: var(--bg); font-weight: 600; }
    tr:hover { background: #f9f9f9; }
    .actions { display: flex; gap: 10px; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>⚙️ Admin Panel</h1>
      <a href="/" class="back-link">← Asosiy sahifa</a>
    </header>

    <div class="card">
      <h2 style="margin-bottom: 20px;">➕ Yangi mavzu qo'shish</h2>
      <form action="/admin/add" method="POST">
        <div class="form-group">
          <label>Mavzu nomi:</label>
          <input type="text" name="title" required>
        </div>
        <div class="form-group">
          <label>Python fayl nomi (masalan: topic11.py):</label>
          <input type="text" name="file" required>
        </div>
        <button type="submit" class="btn btn-primary">Qo'shish</button>
      </form>
    </div>


    <div class="card">
      <h2 style="margin-bottom: 20px;">📋 Mavzular ro'yxati</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Mavzu nomi</th>
            <th>Python fayl</th>
            <th>Amallar</th>
          </tr>
        </thead>
        <tbody>
          {% for id, topic in topics.items() %}
          <tr>
            <td>{{ id }}</td>
            <td>{{ topic.title }}</td>
            <td>{{ topic.file }}</td>
            <td class="actions">
              <form action="/admin/delete/{{ id }}" method="POST" style="display: inline;">
                <button type="submit" class="btn btn-danger" onclick="return confirm('O\\'chirishni tasdiqlaysizmi?')">🗑 O'chirish</button>
              </form>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>'''


@app.route('/')
def index():
    return render_template_string(FRONTEND_HTML, topics=topics)


@app.route('/admin')
def admin():
    return render_template_string(ADMIN_HTML, topics=topics)


@app.route('/admin/add', methods=['POST'])
def add_topic():
    title = request.form.get('title')
    file = request.form.get('file')

    new_id = max(topics.keys()) + 1 if topics else 1
    topics[new_id] = {"title": title, "file": file}

    return redirect('/admin')


@app.route('/admin/delete/<int:topic_id>', methods=['POST'])
def delete_topic(topic_id):
    if topic_id in topics:
        # Agar jarayon ishlab tursa, to'xtatish
        with process_lock:
            if topic_id in running_processes:
                running_processes[topic_id].terminate()
                del running_processes[topic_id]

        del topics[topic_id]

    return redirect('/admin')


@app.route('/run/<int:topic_id>', methods=['POST'])
def run_topic(topic_id):
    if topic_id not in topics:
        return jsonify({"success": False, "message": "Mavzu topilmadi"})

    topic = topics[topic_id]
    file_path = topic['file']

    if not os.path.exists(file_path):
        return jsonify({"success": False, "message": f"Fayl topilmadi: {file_path}"})

    with process_lock:
        if topic_id in running_processes:
            if running_processes[topic_id].poll() is None:
                return jsonify({"success": False, "message": "Dastur allaqachon ishga tushirilgan"})
            else:
                del running_processes[topic_id]

        try:
            # Natijani o'qish uchun PIPE ishlatamiz (timeout o'chirilgan)
            process = subprocess.Popen(
                ['python', file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            running_processes[topic_id] = process

            # Timeout parametri olib tashlandi - dastur tugaguncha kutadi
            stdout, stderr = process.communicate()
            message = stdout if stdout else stderr
            return jsonify({"success": True, "message": message})
        except Exception as e:
            return jsonify({"success": False, "message": f"Xatolik: {str(e)}"})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
