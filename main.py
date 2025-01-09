import webview
import psutil
import sqlite3
import datetime
import threading
import time
from flask import Flask, jsonify, render_template
from flask_cors import CORS
import atexit
import platform


# Путь к базе данных
database_path = 'data.sql'

# Flask app
app = Flask(__name__)
CORS(app)

DATA_COLLECTION_INTERVAL = 10 * 60  # 10 минут в секундах
APP_DATA_COLLECTION_INTERVAL = 60 # 60 секунд
def create_database():
    """Создает базу данных и таблицы, если их нет."""
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cpu_data (
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            cpu_usage REAL,
            top_app TEXT
        )
    """)
    try:
        cursor.execute("ALTER TABLE cpu_data ADD COLUMN top_app TEXT")
    except sqlite3.OperationalError:
        print("Столбец top_app уже существует.")
    cursor.execute("""
           CREATE TABLE IF NOT EXISTS app_usage (
               timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
               app_name TEXT,
               duration INTEGER
           )
       """)
    cursor.execute("""
           CREATE TABLE IF NOT EXISTS system_info (
              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
               os_name TEXT,
               cpu_model TEXT,
               ram_total INTEGER
           )
       """)
    cursor.execute("""
           CREATE TABLE IF NOT EXISTS user_activity (
               timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
               event_type TEXT,
               event_detail TEXT
           )
       """)

    conn.commit()
    conn.close()

def get_system_info():
    """Получает и возвращает информацию о системе."""
    os_name = platform.system() + " " + platform.release()
    cpu_model = platform.processor()
    ram_total = psutil.virtual_memory().total / (1024 ** 2) # в мб
    return os_name, cpu_model, ram_total

def collect_system_info_and_store():
    """Собирает данные о системе и сохраняет их в БД."""
    os_name, cpu_model, ram_total = get_system_info()
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM system_info")
    count = cursor.fetchone()[0]
    if count == 0: # первый запуск
         cursor.execute("INSERT INTO system_info (os_name, cpu_model, ram_total) VALUES (?, ?, ?)",
                     (os_name, cpu_model, ram_total))
         conn.commit()
    else: # проверяем на изменения
        cursor.execute("SELECT os_name, cpu_model, ram_total FROM system_info ORDER BY timestamp DESC LIMIT 1")
        last_info = cursor.fetchone()
        if last_info[0] != os_name or last_info[1] != cpu_model or last_info[2] != ram_total:
             cursor.execute("INSERT INTO system_info (os_name, cpu_model, ram_total) VALUES (?, ?, ?)",
                      (os_name, cpu_model, ram_total))
             conn.commit()
    conn.close()



def get_current_cpu_data():
    """Получает текущие данные о загрузке CPU и самом ресурсозатратном приложении."""
    cpu_usage = psutil.cpu_percent(interval=1)
    # Получаем список процессов, отсортированных по использованию CPU
    processes = sorted(
        psutil.process_iter(['name', 'cpu_percent']),
        key=lambda p: p.info['cpu_percent'] or 0,
        reverse=True
    )
    top_app = processes[0].info['name'] if processes else "N/A"

    return cpu_usage, top_app

def collect_data_and_store():
    """Собирает данные о CPU и сохраняет их в базу данных каждые 10 минут."""
    while True:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        cpu_usage, top_app = get_current_cpu_data()

        cursor.execute("INSERT INTO cpu_data (cpu_usage, top_app) VALUES (?, ?)",
                       (cpu_usage, top_app))
        conn.commit()
        conn.close()

        time.sleep(DATA_COLLECTION_INTERVAL)  # Задержка 10 минут

def collect_app_data():
    """Собирает данные об использовании приложений и сохраняет их в БД."""
    while True:
      conn = sqlite3.connect(database_path)
      cursor = conn.cursor()
      processes = sorted(
          psutil.process_iter(['name', 'create_time']),
          key=lambda p: p.info['create_time'] or 0,
      )
        # сохраняем время создания процесса
      for process in processes:
           if not hasattr(process, 'start_time'):
                try:
                    process.start_time = datetime.datetime.fromtimestamp(process.info['create_time']).replace(microsecond=0)
                except (OSError,TypeError):
                    continue

           else:
                try:
                    duration = (datetime.datetime.now().replace(microsecond=0) - process.start_time).total_seconds()
                    cursor.execute("INSERT INTO app_usage (app_name, duration) VALUES (?, ?)",(process.info['name'], duration))
                    conn.commit()
                except (OSError,TypeError):
                    continue
      conn.close()
      time.sleep(APP_DATA_COLLECTION_INTERVAL)

def record_user_activity(event_type, event_detail=""):
    """Записывает действия пользователя в таблицу `user_activity`."""
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_activity (event_type, event_detail) VALUES (?, ?)", (event_type, event_detail))
    conn.commit()
    conn.close()

@app.route('/current_data')
def current_data():
    cpu_usage, top_app = get_current_cpu_data()
    data = {
        'cpu_usage': cpu_usage,
        'top_app': top_app
    }
    return jsonify(data)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chart_data')
def chart_data():
     conn = sqlite3.connect(database_path)
     cursor = conn.cursor()
     cursor.execute("SELECT timestamp, cpu_usage, top_app FROM cpu_data")
     data = cursor.fetchall()
     conn.close()
     chart_data_list = []
     for row in data:
          chart_data_list.append(
               {
                 "timestamp":row[0],
                  "cpu_usage":row[1],
                  "top_app":row[2]
               }
          )
     return jsonify(chart_data_list)
@app.route('/app_usage_data')
def app_usage_data():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, app_name, duration FROM app_usage")
    data = cursor.fetchall()
    conn.close()
    app_usage_data_list = []
    for row in data:
        app_usage_data_list.append({
              "timestamp": row[0],
               "app_name": row[1],
               "duration": row[2]
          }
        )
    return jsonify(app_usage_data_list)
@app.route('/system_info_data')
def system_info_data():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, os_name, cpu_model, ram_total FROM system_info")
    data = cursor.fetchall()
    conn.close()
    system_info_data_list = []
    for row in data:
        system_info_data_list.append(
            {
                "timestamp": row[0],
                "os_name": row[1],
                "cpu_model": row[2],
                "ram_total": row[3]
            }
        )
    return jsonify(system_info_data_list)
@app.route('/user_activity_data')
def user_activity_data():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, event_type, event_detail FROM user_activity")
    data = cursor.fetchall()
    conn.close()
    user_activity_data_list = []
    for row in data:
        user_activity_data_list.append(
            {
                "timestamp": row[0],
                "event_type": row[1],
                "event_detail": row[2]
            }
        )
    return jsonify(user_activity_data_list)

@app.route('/app_usage')
def app_usage():
    record_user_activity("open app usage window")
    return render_template('app_usage.html')

@app.route('/system_info')
def system_info():
    record_user_activity("open system info window")
    return render_template('system_info.html')

@app.route('/user_activity')
def user_activity():
    record_user_activity("open user activity window")
    return render_template('user_activity.html')

def run_server():
    """Запускает Flask-сервер."""
    app.run(debug=False, port=5001, use_reloader=False)
def delete_data_from_db():
     """Удаляет все данные из БД при закрытии."""
     conn = sqlite3.connect(database_path)
     cursor = conn.cursor()
     cursor.execute("DELETE FROM cpu_data")
     cursor.execute("DELETE FROM app_usage")
     cursor.execute("DELETE FROM system_info")
     cursor.execute("DELETE FROM user_activity")
     conn.commit()
     conn.close()
if __name__ == '__main__':
    create_database()
    threading.Thread(target=run_server, daemon=True).start()
    threading.Thread(target=collect_data_and_store, daemon=True).start()
    threading.Thread(target=collect_app_data, daemon=True).start()
    threading.Thread(target=collect_system_info_and_store, daemon=True).start()
    atexit.register(delete_data_from_db)
    webview.create_window("CPUViewer", "http://127.0.0.1:5001/")
    webview.start()