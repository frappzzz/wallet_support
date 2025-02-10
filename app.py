from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO
from DB import DB
import eventlet
import requests

app = Flask(__name__, static_folder="www/files", template_folder="www")
app.config['SECRET_KEY'] = 'secrsssset!'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")
BOT_TOKEN = "8041525340:AAGiUjdpl7ZmDc5IO5YvATfXgBRXI_DRCz8"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Правильные логин и пароль
CORRECT_USERNAME = "admin"
CORRECT_PASSWORD = "AdminA487"


@app.route('/')
def index():
    # Проверяем, авторизован ли пользователь
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    db = DB()
    users = db.get_all_users() # Получаем уникальных пользователей
    return render_template('index.html', users=users)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')

        # Проверяем логин и пароль
        if username == CORRECT_USERNAME and password == CORRECT_PASSWORD:
            session['logged_in'] = True
            return jsonify({'success': True})
        else:
            return jsonify({'success': False})

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/generate_link/<int:id_user_web>')
def generate_link(id_user_web):
    bot_username = "hammysupport_bot"  # Замените на username бота
    return f"https://t.me/{bot_username}?start={id_user_web}"
@app.route('/new_user', methods=['POST'])
def handle_new_user():
    data = request.json
    socketio.emit('new_user', {
        'id_user_tg': data['id_user_tg'],
        'id_user_web': data['id_user_web']
    })
    return jsonify({'status': 'success'})

@app.route('/get_messages/<int:id_user_tg>')
def get_messages(id_user_tg):
    db = DB()
    user_messages = db.get_messages_by_user(id_user_tg)
    bot_messages = db.get_messages_by_bot(id_user_tg)

    combined = []
    for msg in user_messages:
        combined.append({
            'type': 'user',
            'message': msg[3],
            'number': msg[4]
        })
    for msg in bot_messages:
        combined.append({
            'type': 'bot',
            'message': msg[2],
            'number': msg[3]
        })

    combined.sort(key=lambda x: x['number'])
    return jsonify(combined)
@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    id_user_tg = data['id_user_tg']
    bot_message = data['message']

    db = DB()
    last_message_number = db.get_last_user_message_number(id_user_tg)
    db.addBotMessage(id_user_tg, bot_message, last_message_number + 1)

    # Отправка сообщения в Telegram
    try:
        response = requests.post(TELEGRAM_API_URL, json={
            "chat_id": id_user_tg,
            "text": bot_message
        })
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return jsonify({'status': 'error', 'error': str(e)})

    # Обновление чата в веб-интерфейсе
    socketio.emit('update_messages', {
        'id_user_tg': id_user_tg,
        'message': bot_message,
        'type': 'bot'
    })
    return jsonify({'status': 'success'})

@app.route('/new_message', methods=['POST'])
def new_message():
    data = request.json
    id_user_tg = data['id_user_tg']
    user_message = data['message']

    # Отправляем обновление сообщений в браузер
    socketio.emit('update_messages', {
        'id_user_tg': id_user_tg,
        'message': user_message,
        'type': 'user'
    })

    return jsonify({'status': 'success'})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0',port=5005, debug=True)
