import sqlite3
from flask import Flask, jsonify
import time

app = Flask(__name__)

database_path = 'data.sql'

@app.route('/')
def index():
    """Обработчик для корневого URL."""
    return "Flask server is running!"

@app.route('/get_data')
def get_data():
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, cpu_usage, top_app FROM cpu_data")
        rows = cursor.fetchall()
        conn.close()

        data = []
        for row in rows:
            data.append({
                'timestamp': row[0],
                'cpu_usage': row[1],
                'top_app': row[2]
         })
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8080)