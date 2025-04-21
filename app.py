
from flask import Flask, render_template_string, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecret'

# 初始化資料庫
conn = sqlite3.connect('components.db')
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT,
    component_id TEXT,
    serial_number TEXT,
    install_date TEXT,
    x1 TEXT,
    x2 TEXT,
    y1 TEXT,
    y2 TEXT
)""")
conn.commit()
conn.close()

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>構件吊裝紀錄系統</title>
</head>
<body>
    <h1>構件吊裝紀錄系統</h1>

    <h2>新增構件紀錄</h2>
    <form method='POST' action='/add'>
        專案名稱:
        <select name='project_name'>
            <option value='AP7P1'>AP7P1</option>
            <option value='AP7P2'>AP7P2</option>
            <option value='Office'>Office</option>
        </select><br>

        吊裝日期: <input type='date' name='install_date' value='{{ today }}'><br>

        構件編號: <input type='text' name='component_id' value='{{ component_id | default('') }}'><br>
        流水號（可批量，範例: 152-155,172-175）: <input type='text' name='serial_number' value='{{ serial_number | default('') }}'><br>

        吊裝位置：<br>
        Line線(英文)：<select name='x1'>{{ options_alpha|safe }}</select>
        到 <select name='x2'>{{ options_alpha|safe }}</select><br>
        Line線(數字)：<select name='y1'>{{ options_number|safe }}</select>
        到 <select name='y2'>{{ options_number|safe }}</select><br>

        <input type='submit' name='action' value='新增'>
        <input type='submit' name='action' value='上一筆'>
    </form>

    <h2>查詢構件紀錄</h2>
    <form method='GET' action='/search'>
        構件編號: <input type='text' name='component_id'><br>
        流水號: <input type='text' name='serial_number'><br>
        <input type='submit' value='查詢'>
    </form>

    {% if result %}
        <h3>查詢結果</h3>
        <p>專案名稱: {{ result[0] }}</p>
        <p>構件編號: {{ result[1] }}</p>
        <p>流水號: {{ result[2] }}</p>
        <p>吊裝日期: {{ result[3] }}</p>
        <p>吊裝位置: <span style='color:#0000FF'>{{ result[4] }}-{{ result[5] }}</span>/<span style='color:#0000FF'>{{ result[6] }}-{{ result[7] }}</span></p>
    {% elif searched %}
        <p>查無資料</p>
    {% endif %}
</body>
</html>
"""

def generate_alpha_options():
    values = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
    full = []
    for val in values:
        full.append(val)
        full.append(val + ".5")
    return "".join([f"<option value='{v}'>{v}</option>" for v in full])

def generate_number_options():
    values = [str(i) for i in range(1, 19)]
    full = []
    for v in values:
        full.append(v)
        full.append(v + ".5")
    return "".join([f"<option value='{v}'>{v}</option>" for v in full])

def parse_serial_ranges(text):
    ranges = []
    parts = text.replace(' ', '').split(',')
    for part in parts:
        if '-' in part:
            start, end = map(int, part.split('-'))
            ranges.extend([str(i) for i in range(start, end + 1)])
        else:
            ranges.append(part)
    return ranges

@app.route('/')
def index():
    today = datetime.today().strftime('%Y-%m-%d')
    session_defaults = {
        'component_id': '',
        'serial_number': '',
        'x1': '',
        'x2': '',
        'y1': '',
        'y2': ''
    }
    last = session.get('last_input', session_defaults)
    return render_template_string(html_template,
                                  today=today,
                                  options_alpha=generate_alpha_options(),
                                  options_number=generate_number_options(),
                                  result=None,
                                  searched=False,
                                  **last)

@app.route('/add', methods=['POST'])
def add_component():
    action = request.form['action']
    if action == '上一筆':
        session['last_input'] = {
            'component_id': request.form['component_id'],
            'serial_number': request.form['serial_number'],
            'x1': request.form['x1'],
            'x2': request.form['x2'],
            'y1': request.form['y1'],
            'y2': request.form['y2']
        }
        return redirect('/')

    serials = parse_serial_ranges(request.form['serial_number'])

    # 按下「新增」後清空欄位
    session['last_input'] = {
        'component_id': '',
        'serial_number': '',
        'x1': '',
        'x2': '',
        'y1': '',
        'y2': ''
    }

    conn = sqlite3.connect('components.db')
    c = conn.cursor()
    for serial in serials:
        data = (
            request.form['project_name'],
            request.form['component_id'],
            serial,
            request.form['install_date'],
            request.form['x1'],
            request.form['x2'],
            request.form['y1'],
            request.form['y2']
        )
        c.execute('INSERT INTO components (project_name, component_id, serial_number, install_date, x1, x2, y1, y2) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', data)
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/search', methods=['GET'])
def search():
    component_id = request.args.get('component_id')
    serial_number = request.args.get('serial_number')
    conn = sqlite3.connect('components.db')
    c = conn.cursor()
    c.execute('SELECT project_name, component_id, serial_number, install_date, x1, x2, y1, y2 FROM components WHERE component_id=? AND serial_number=?', (component_id, serial_number))
    result = c.fetchone()
    conn.close()
    return render_template_string(html_template,
                                  today=datetime.today().strftime('%Y-%m-%d'),
                                  options_alpha=generate_alpha_options(),
                                  options_number=generate_number_options(),
                                  result=result, searched=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
