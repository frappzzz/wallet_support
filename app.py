from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO
from DB import DB
import config
import eventlet
import requests
import random
import string


app = Flask(__name__, static_folder="www/files", template_folder="www")
app.config['SECRET_KEY'] = config.SECRET_KEY
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")
BOT_TOKEN = config.TG_BOT_TOKEN
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Правильные логин и пароль
CORRECT_USERNAME = config.APP_CORRECT_USERNAME
CORRECT_PASSWORD = config.APP_CORRECT_PASSWORD

@app.route('/')
def index():
    # Проверяем, авторизован ли пользователь
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    db = DB()
    users = db.get_all_users() # Получаем уникальных пользователей
    return render_template('index.html', users=users)


def generate_token():
    # Генерация токена: {буква}{3 цифры}{3 буквы}
    letter = random.choice(string.ascii_uppercase)
    digits = ''.join(random.choice(string.digits) for _ in range(3))
    letters = ''.join(random.choice(string.ascii_uppercase) for _ in range(3))
    return f"{letter}{digits}{letters}"

@app.route('/generate_tg_key', methods=['POST'])
def generate_tg_key():
    data = request.json
    id_user_web = data.get('id_user_web')

    if not id_user_web:
        return jsonify({'error': 'id_user_web is required'}), 400

    db = DB()
    user = db.get_user_by_web_id(id_user_web)
    if user:  # Если id_user_tg уже есть
        token = user[1]
    else:
        token = generate_token()
        db.add_user_with_token(id_user_web, token)

    bot_username = "hammysupport_bot"
    url = f"https://t.me/{bot_username}?start={token}"
    return jsonify({'url': url}), user
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')

        # Отправляем запрос на внешний API для проверки логина и пароля
        auth_url = "http://195.2.79.241:5000/api_adm/user_auth"
        try:
            response = requests.post(auth_url, json={"login": username, "password": password})
            response_data = response.json()

            # Проверяем ответ от API
            if response_data.get("login") == "True" and response_data.get("password") == "True" and response_data.get("status") in [8, 9]:
                session['logged_in'] = True
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Ошибка авторизации'})
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе к API: {e}")
            return jsonify({'success': False, 'error': 'Ошибка при запросе к API'})

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
