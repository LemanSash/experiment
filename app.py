from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3, random, json
from itertools import permutations
import psycopg2
import psycopg2.extras
import logging
import bcrypt
from logging.handlers import RotatingFileHandler
from werkzeug.serving import run_simple
from datetime import datetime, timedelta, timezone
import smtplib
from email.message import EmailMessage
import jwt
from dotenv import load_dotenv
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2000 per day", "1000 per hour", "120 per minute"],
    storage_uri="memory://",
)


load_dotenv()  # Загружает переменные окружения из файла .env

SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
APP_SECRET_KEY = os.getenv('APP_SECRET_KEY')
SMTP_SECRET_KEY = os.getenv('SMTP_SECRET_KEY')
DB_PASSWORD = os.getenv('DB_PASSWORD')
LOGGING_DIRECTORY = os.getenv('LOGGING_DIRECTORY')

app.secret_key = APP_SECRET_KEY
SECRET_KEY = SMTP_SECRET_KEY

app.config.update({
    'SESSION_COOKIE_SECURE': True,  # Безопасность сессий (SSL/TLS обязателен!)
    'SESSION_COOKIE_HTTPONLY': True,  # Доступ к куки возможен только через HTTP
    'PERMANENT_SESSION_LIFETIME': timedelta(hours=1)  # Сессия заканчивается при закрытии браузера
})

LOGGING_PATH = '/var/www/experiment/logs/flask_app.log'
if LOGGING_DIRECTORY is not None:
    LOGGING_PATH = LOGGING_DIRECTORY + '/flask_app.log'
# Если используешь Gunicorn, интегрируй его логгер
if __name__ != "__main__":
    g_logger = logging.getLogger("gunicorn.error")
    handler = RotatingFileHandler(LOGGING_PATH, maxBytes=10000, backupCount=1)
    g_logger.addHandler(handler)
    g_logger.setLevel(logging.INFO)
else:
    handler = RotatingFileHandler(LOGGING_PATH, maxBytes=10000, backupCount=1)
    logger = logging.getLogger('werkzeug')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    app.logger.addHandler(handler)

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception(str(e))  # Это гарантирует сохранение полной трассировки стека
    return "Internal Server Error", 500


# @app.before_request
# def before_request():
#     # Разрешите пропуск проверок для маршрутов авторизации и регистрации
#     allowed_routes = ['login', 'register', 'logout', 'home']
#     if request.endpoint not in allowed_routes and 'user_id' not in session:
#         flash('Session lost. Please log in again.')
#         return redirect(url_for('login'))

# Helper function to get database connection
def get_db():
    conn = psycopg2.connect(
        dbname="experiment_db",
        user="admin",
        password=DB_PASSWORD,
        host="localhost",
        port=5432
    )
    return conn

# Initialize database and create tables
def init_db():
    conn = get_db()
    conn.autocommit = False
    cursor = conn.cursor()

    # cursor.execute('DROP TABLE IF EXISTS user_sequences CASCADE')
    # cursor.execute('DROP TABLE IF EXISTS users CASCADE')
    # cursor.execute('TRUNCATE TABLE bart_results RESTART IDENTITY CASCADE')
    # cursor.execute('TRUNCATE TABLE user_progress RESTART IDENTITY CASCADE')
    # cursor.execute('TRUNCATE TABLE tasks_questions RESTART IDENTITY CASCADE')
    # cursor.execute('TRUNCATE TABLE cct_hot_results RESTART IDENTITY CASCADE')
    # cursor.execute('TRUNCATE TABLE cct_cold_results RESTART IDENTITY CASCADE')
    # cursor.execute('TRUNCATE TABLE igt_results RESTART IDENTITY CASCADE')
    #Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            age INTEGER,
            gender TEXT,
            education TEXT
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cct_hot_results (
            result_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            trial_number INTEGER NOT NULL,
            trial_type TEXT NOT NULL,
            decision INTEGER NOT NULL,
            result TEXT,
            flip_number INTEGER,
            current_points INTEGER,
            points INTEGER,
            reaction_time INTEGER,
            loss_cards INTEGER,
            gain_amount INTEGER,
            loss_amount INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cct_cold_results (
            result_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            trial_number INTEGER,
            num_cards INTEGER,
            loss_encountered BOOLEAN,
            points_earned INTEGER,
            reaction_time INTEGER,
            loss_cards INTEGER,
            gain_amount INTEGER,
            loss_amount INTEGER
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS igt_results (
            result_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            trial_number INTEGER,
            deck TEXT,
            payout INTEGER,
            penalty INTEGER,
            points_earned INTEGER,
            reaction_time INTEGER
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bart_results (
            result_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            trial_number INTEGER,
            pump_number INTEGER,
            break_point INTEGER,
            popped BOOLEAN,
            points_earned INTEGER,
            total_points INTEGER,
            reaction_time INTEGER
        );
    ''')

    # cursor.execute('''
    #     CREATE TABLE IF NOT EXISTS bart_results (
    #         result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         user_id INTEGER NOT NULL,
    #         trial_number INTEGER NOT NULL,
    #         pump_number INTEGER NOT NULL,
    #         break_point INTEGER NOT NULL,
    #         popped BOOLEAN NOT NULL,
    #         points_earned INTEGER NOT NULL,
    #         total_points INTEGER NOT NULL,
    #         reaction_time INTEGER NOT NULL
    #     )
    #     '''
    # )

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questionnaire_responses (
            response_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            question_number INTEGER NOT NULL,
            response INTEGER NOT NULL
        );
    ''')

    # Create sequences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sequences (
            sequence_id SERIAL PRIMARY KEY,
            task1 TEXT NOT NULL,
            task2 TEXT NOT NULL,
            task3 TEXT NOT NULL,
            task4 TEXT NOT NULL,
            assigned_count INTEGER DEFAULT 0
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sequences (
            user_id INTEGER REFERENCES users(user_id),
            task1 TEXT,
            task2 TEXT,
            task3 TEXT,
            task4 TEXT,
            feedback_type TEXT
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            user_id INTEGER REFERENCES users(user_id),
            task_name TEXT NOT NULL,
            device_type TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, task_name)
        );
    ''')

    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS sequences_unique
            ON sequences (task1, task2, task3, task4);
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS risk_aversion_responses (
            response_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            question_number INTEGER NOT NULL,
            response INTEGER NOT NULL
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks_questions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            task_name TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rfq_responses (
            response_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            question_number INTEGER NOT NULL,
            response INTEGER NOT NULL
        );
    ''')

    # Populate sequences table
    methods = ["igt", "bart", "cct_hot", "cct_cold"]  # Use endpoint names
    all_sequences = list({p for p in permutations(methods)})  # Get unique permutations
    for seq in all_sequences[:16]:  # Use first 16 unique sequences
        cursor.execute("""
            INSERT INTO sequences (task1, task2, task3, task4)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (task1, task2, task3, task4) DO NOTHING
        """, seq)
        # with conn.transaction(isolation_level='serializable'):
        #     cursor.execute("""
        #         INSERT INTO sequences (task1, task2, task3, task4)
        #         VALUES (%s, %s, %s, %s)
        #         ON CONFLICT (task1, task2, task3, task4) DO NOTHING
        #     """, seq)

    conn.commit()
    conn.close()

init_db()

# @app.before_request
# def check_session():
#     if 'user_id' not in session:
#         session['user_id'] = None
#     if 'completed_tasks' not in session:
#         session['completed_tasks'] = []
#     if 'sequence' not in session:
#         session['sequence'] = []

@app.before_request
def check_session():
    if 'user_id' not in session or session['user_id'] is None:
        session.pop('user_id', None)  # Полностью удалить ключ
    if 'completed_tasks' not in session:
        session['completed_tasks'] = []
    if 'sequence' not in session:
        session['sequence'] = []

@app.before_request
def before_request():
    # Пропускаем проверку для запросов к статическим файлам
    if request.path.startswith('/static/'):
        return

    # Разрешить пропуска проверок для маршрутов авторизации и регистрации
    allowed_routes = ['login', 'register', 'logout', 'index', 'terms', 'agreement', 'reset_password_request',
                      'reset_password']

    # Если текущий запрос не входит в разрешённые маршруты и пользователь не залогинен
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        flash('Session lost. Please log in again.')
        return redirect(url_for('login'))

def get_device_type():
    ua = request.user_agent
    # Простейший набор платформ‑маркеров
    mobile_plats = {'iphone', 'ipad', 'android'}
    if ua.platform and ua.platform.lower() in mobile_plats:
        return 'mobile'
    # fallback по строке
    if 'mobile' in ua.string.lower():
        return 'mobile'
    return 'desktop'


# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if not request.form.get('agree_terms'):
            flash('Необходимо принять условия участия', 'danger')
            return redirect(url_for('register'))
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        age = request.form['age']
        gender = request.form['gender']
        education = request.form['education']
        # Hash the password (use a library like bcrypt in production)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, age, gender, education)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                request.form['username'],
                password_hash,  # TODO: hash
                request.form['email'], 
                request.form['age'],
                request.form['gender'],
                request.form['education']
            ))
            conn.commit()
            return redirect(url_for('login'))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("Username already exists")
        finally:
            cursor.close()
            conn.close()
    print('Oops.')
    return render_template('register.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/agreement')
def agreement():
    return render_template('agreement.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, password_hash
            FROM users
            WHERE username = %s
        """, (username,))
        user = cursor.fetchone()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            session['user_id'] = user[0]
            cursor.execute("""
                SELECT task_name
                FROM user_progress
                WHERE user_id = %s
            """, (user[0],))
            completed_tasks = [row[0] for row in cursor.fetchall()]
            session['completed_tasks'] = completed_tasks
            cursor.close()
            conn.close()
            flash('Login successfull!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username of password.')
        cursor.close()
        conn.close()
    return render_template('login.html')

def generate_reset_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=1)  # Срок действия токена: 1 час
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def verify_reset_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None  # Токен просрочен
    except jwt.InvalidTokenError:
        return None  # Недопустимый токен

def send_reset_email(email, token):
    msg = EmailMessage()
    msg.set_content(f'''
        Нажмите на следующую ссылку для сброса вашего пароля:
        {url_for('reset_password', token=token, _external=True)}
    ''')
    
    msg['Subject'] = 'Восстановление пароля'
    msg['From'] = 'info@decision-making-research.ru'
    msg['To'] = email
    
    server = smtplib.SMTP_SSL('smtp.beget.com', 465)
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    server.send_message(msg)
    server.quit()

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form['email']
        
        # Проверка существования пользователя с таким email
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        
        if user:
            # Генерация уникального токена для сброса пароля
            token = generate_reset_token(user[0])
            
            # Отправка письма с ссылкой на сброс пароля
            send_reset_email(email, token)
            
            flash('На ваш адрес электронной почты отправлено письмо с инструкциями по восстановлению пароля.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Пользователь с таким электронным адресом не найден.', 'warning')
    
    return render_template('reset_password_request.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Проверка валидности токена
    user_id = verify_reset_token(token)
    
    if not user_id:
        flash('Недопустимый или истекший токен.', 'warning')
        return redirect(url_for('reset_password_request'))
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Пароли не совпадают.', 'warning')
        else:
            # Обновление пароля в базе данных
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash=%s WHERE user_id=%s", (hashed_password.decode('utf-8'), user_id))
            conn.commit()
            
            flash('Ваш пароль успешно сброшен!', 'success')
            return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    task_names = {
        'igt': 'Выбор одной карты из четырёх',
        'bart': 'Надуть шарик',
        'cct_hot': 'Выбрать N карт последовательно',
        'cct_cold': 'Выбрать N карт одновременно'
    }

    conn = get_db()
    cursor = conn.cursor()

    # 1. Получаем или назначаем последовательность заданий
    cursor.execute("""
        SELECT task1, task2, task3, task4
        FROM user_sequences
        WHERE user_id = %s
    """, (user_id,))
    seq_row = cursor.fetchone()

    if not seq_row:
        cursor.execute("""
            SELECT sequence_id, task1, task2, task3, task4
            FROM sequences
            ORDER BY assigned_count ASC, sequence_id ASC
            LIMIT 1
        """)
        sequence = cursor.fetchone()

        if not sequence:
            cursor.close()
            conn.close()
            flash('Нет доступных последовательностей')
            return redirect(url_for('login'))
        
        # Определим тип фидбэка
        cursor.execute("""
            SELECT COUNT(*) FROM user_sequences WHERE feedback_type = 'first_feedback'
        """)
        with_feedback_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM user_sequences WHERE feedback_type = 'last_feedback'
        """)
        without_feedback_count = cursor.fetchone()[0]

        # Балансируем типы фидбэка
        if with_feedback_count > without_feedback_count:
            feedback = 'last_feedback'
        elif with_feedback_count <= without_feedback_count:
            feedback = 'first_feedback'
        else:
            feedback = random.choice(['first_feedback', 'last_feedback'])

        cursor.execute("""
            INSERT INTO user_sequences (user_id, task1, task2, task3, task4, feedback_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, sequence[1], sequence[2], sequence[3], sequence[4], feedback))

        conn.commit()

        cursor.execute("""
            UPDATE sequences
            SET assigned_count = assigned_count + 1
            WHERE sequence_id = %s
        """, (sequence[0],))

        conn.commit()
        sequence = [sequence[1], sequence[2], sequence[3], sequence[4]]
    else:
        sequence = list(seq_row)

    session['sequence'] = sequence

    # 2. Проверяем, заполнена ли анкета
    cursor.execute("""
        SELECT 1
        FROM questionnaire_responses
        WHERE user_id = %s
        LIMIT 1
    """, (user_id,))
    has_first_questionnaire = cursor.fetchone() is not None

    # 3. Проверяем, заполнена ли вторая анкета
    cursor.execute("""
        SELECT 1
        FROM risk_aversion_responses
        WHERE user_id = %s
        LIMIT 1
    """, (user_id,))
    has_second_questionnaire = cursor.fetchone() is not None

    # 3. Проверяем, заполнена ли вторая анкета
    cursor.execute("""
        SELECT 1
        FROM rfq_responses
        WHERE user_id = %s
        LIMIT 1
    """, (user_id,))
    has_third_questionnaire = cursor.fetchone() is not None

    # 3. Загружаем завершённые задания
    cursor.execute("""
        SELECT task_name
        FROM user_progress
        WHERE user_id = %s
    """, (user_id,))
    completed_tasks = [row[0] for row in cursor.fetchall()]
    session['completed_tasks'] = completed_tasks

    # 4. Последняя активность
    cursor.execute("""
        SELECT MAX(completed_at)
        FROM user_progress
        WHERE user_id = %s
    """, (user_id,))
    
    last_active_utc = cursor.fetchone()[0]
    if last_active_utc is None:
        last_active = "Нет активности"
    else:
        # Преобразование в московское время (+3 часа)
        local_time = last_active_utc.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=3)))
        # Формируем требуемый формат: YYYY-MM-DD HH:MM
        last_active = local_time.strftime('%Y-%m-%d %H:%M')
    

    cursor.close()
    conn.close()

    # 5. Определяем следующее задание
    next_task = None
    if has_first_questionnaire and has_second_questionnaire and has_third_questionnaire:
        # Если обе анкеты завершены, выбираем игровое задание
        for task in sequence:
            if task not in completed_tasks:
                next_task = task
                break
    elif has_first_questionnaire and not has_second_questionnaire and not has_third_questionnaire:
        # Вторая анкета ещё не заполнена
        next_task = 'second_questionnaire'
    elif has_second_questionnaire and has_first_questionnaire and not has_third_questionnaire:
        next_task = 'third_questionnaire'
    else:
        # Первая анкета ещё не заполнена
        next_task = 'questionnaire'

    # 6. Результаты (если есть)
    results_dict = {}
    total = 0
    if completed_tasks:
        results_dict, total = get_user_results(user_id)

    return render_template(
        'dashboard.html',
        #has_questionnaire=has_questionnaire,
        has_first_questionnaire=has_first_questionnaire,
        has_second_questionnaire=has_second_questionnaire,
        has_third_questionnaire=has_third_questionnaire,
        next_task=next_task,
        completed_tasks=completed_tasks,
        sequence=sequence,
        last_active=last_active,
        task_names=task_names,
        results=results_dict,
        total=total
    )


@app.route('/start_experiment', methods=['POST'])
def start_experiment():
    user_id = session.get('user_id')
    print(f"Current user_id in session: {user_id}")  # Добавлено для дебага
    if not user_id:
        return redirect(url_for('login'))

    return redirect(url_for('questionnaire'))

@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    print(f"Sequence in session: {session.get('sequence')}")  # Debugging
    if 'sequence' not in session:
        flash('No sequence assigned. Please start the experiment again.')
        return redirect(url_for('dashboard'))

    QUESTIONS = [
    "Я «ерзаю» во время представлений и лекций.",
    "Я неусидчив(а) в театре или на лекциях.",
    "Я невнимательный(-ая).",
    "Я легко сосредоточиваюсь.",
    "Я мыслю последовательно.",
    "Я импульсивен(-на).",
    "Я действую по обстоятельствам.",
    "Я импульсивен(-на) в покупках.",
    "У меня быстрое мышление.",
    "Я действую без обдумывания.",
    "Я трачу или прошу больше, чем зарабатываю.",
    "Я беззаботный(-ая), ветреный(-ая).",
    "Я аккуратен(-на), осторожен(-на) в мыслях.",
    "Я тщательно планирую задачи.",
    "Я контролирую себя.",
    "Я планирую поездки задолго до их начала.",
    "Я планирую безопасность работы.",
    "Я говорю, не подумав.",
    "Мне нравится обдумывать сложные проблемы.",
    "Мне нравятся загадки (ребусы).",
    "Я коплю регулярно.",
    "Я более заинтересован(-на) в настоящем, нежели в будущем.",
    "Я скучаю при решении задач, требующих обдумывания.",
    "Я меняю места жительства .",
    "Я меняю работу.",
    "Я ориентирована(-на) на будущее.",
    "Я могу думать лишь об одной проблеме одновременно.",
    "Когда я думаю, у меня возникают посторонние мысли.",
    "Я быстро определяюсь в своем мнении.",
    " Я меняю свои хобби."
]

    if request.method == 'POST':
        # Save the score to the database
        user_id = session.get('user_id')
        conn = get_db()
        cursor = conn.cursor()

        # Save questionnaire responses
        for i in range(1, 31):  # Loop through all 30 questions
            question_key = f'q{i}'
            response = request.form.get(question_key)
            if response:
                # Save the response to the database
                cursor.execute("""
                    INSERT INTO questionnaire_responses (user_id, question_number, response)
                    VALUES (%s, %s, %s)
                """, (user_id, i, int(response)))

        conn.commit()
        cursor.close()
        conn.close()

        # Redirect to the first task
        #return redirect(url_for('task', task_name=session['sequence'][0]))
        return redirect(url_for('second_questionnaire'))

    return render_template('questionnaire.html', questions=QUESTIONS)


@app.route('/second_questionnaire', methods=['GET', 'POST'])
def second_questionnaire():
    if 'sequence' not in session:
        flash('Please start the experiment again.')
        return redirect(url_for('dashboard'))

    SECOND_QUESTIONS = [
        "Я курю (включая сигареты, электронные сигареты, вейпы, кальяны)",
        "Я перехожу дорогу на красный",
        "Я езжу в машине, не пристегивая ремень безопасности",
        "Я выпиваю алкоголь",
        "Я покупаю лотерейные билеты",
        "Я принимаю наркотики",
        "Я делаю ставки (например, на спорт)",
        "Я вкладываю деньги в рискованные проекты (например, стартапы)",
        "Я ввязываюсь в драки",
        "Я использую кредитную (-ые) карту (-ы)",
        "Я занимаюсь опасными видами спорта (например, горнолыжный спорт, прыжки с трамплина, мотоспорт, альпинизм, бейсджампинг)",
        "Я занимаюсь сексом без использования средств контрацепции"
    ]

    if request.method == 'POST':
        # Получаем идентификатор пользователя
        user_id = session.get('user_id')
        conn = get_db()
        cursor = conn.cursor()

        # Сохраняем ответы на вопросы второго опросника
        for i in range(len(SECOND_QUESTIONS)):
            question_key = f'sq{i + 1}'  # sq1, sq2 и т.д.
            response = request.form.get(question_key)
            if response:
                # Сохраняем ответ в базу данных
                cursor.execute("""
                    INSERT INTO risk_aversion_responses (user_id, question_number, response)
                    VALUES (%s, %s, %s)
                """, (user_id, i + 1, int(response)))  # Преобразование ответа в целое число

        conn.commit()
        cursor.close()
        conn.close()

        # Добавляем второй опросник в список завершённых заданий
        session['completed_tasks'].append('second_questionnaire')

        # Далее переходим к первому заданию эксперимента
        # return redirect(url_for('task', task_name=session['sequence'][0]))
        return redirect(url_for('third_questionnaire'))

    return render_template('second_questionnaire.html', second_questions=SECOND_QUESTIONS)

@app.route('/third_questionnaire', methods=['GET', 'POST'])
def third_questionnaire():
    if 'sequence' not in session:
        flash('Please start the experiment again.')
        return redirect(url_for('dashboard'))

    THIRD_QUESTIONS = [
        "Обычно я добиваюсь того, чего хочу",
        "Переходили ли вы в детстве границы дозволенного, делая то, что ваши родители вам запрещали?",
        "Как часто завершение какого-либо дела вдохновляло вас на дальнейшее продолжение работы в этом направлении?",
        "Как часто вы «играли на родительских нервах», когда были ребенком?",
        "Слушались ли вы ваших родителей?",
        "Как часто в детстве вы совершали поступки, которые ваши родители явно не одобряли?",
        "Как часто вы преуспеваете в ваших начинаниях?",
        "Я бываю неосторожен",
        "Как часто при решении важной для вас задачи вам кажется, что вы справляетесь хуже, чем хотели бы?",
        "Я чувствую, что двигаюсь к достижению успеха в своей жизни",
        "В моей жизни мало хобби и увлечений, отвечающих моим интересам, заниматься которыми мне действительно хочется",
    ]

    if request.method == 'POST':
        # Получаем идентификатор пользователя
        user_id = session.get('user_id')
        conn = get_db()
        cursor = conn.cursor()

        # Сохраняем ответы на вопросы второго опросника
        for i in range(len(THIRD_QUESTIONS)):
            question_key = f'sq{i + 1}'  # sq1, sq2 и т.д.
            response = request.form.get(question_key)
            if response:
                # Сохраняем ответ в базу данных
                cursor.execute("""
                    INSERT INTO rfq_responses (user_id, question_number, response)
                    VALUES (%s, %s, %s)
                """, (user_id, i + 1, int(response)))  # Преобразование ответа в целое число

        conn.commit()
        cursor.close()
        conn.close()

        # Добавляем второй опросник в список завершённых заданий
        session['completed_tasks'].append('third_questionnaire')

        # Далее переходим к первому заданию эксперимента
        return redirect(url_for('task', task_name=session['sequence'][0]))

    return render_template('third_questionnaire.html', third_questions=THIRD_QUESTIONS)

# Experimental design parameters
FACTORS = {
    'loss_cards': [1, 2, 3],
    'gain_amount': [10, 30],
    'loss_amount': [250, 750]
}

IGT_PAYOUTS = {
    'A': 100,
    'B': 100,
    'C': 50,
    'D': 50
}

IGT_PENALTY_SCHEMES = {
    'A': [-250]*5 + [0]*5,     # 50%
    'B': [-625]*2 + [0]*8,     # 20%
    'C': [-50]*5 + [0]*5,      # 50%
    'D': [-125]*2 + [0]*8      # 20%
}


def init_igt_decks():
    decks = {}
    for deck, scheme in IGT_PENALTY_SCHEMES.items():
        block = scheme.copy()
        random.shuffle(block)
        decks[deck] = {
            'block': block,
            'index': 0
        }
    return decks

# # Генерируем длинные блоки штрафов для каждой колоды (всего 150 выборов)
# IGT_PENALTY_SCHEMES = {
#     'A': ([0]*75 + [-250]*75),  # 50% штрафов (-250)
#     'B': ([0]*120 + [-625]*30),  # 20% штрафов (-625)
#     'C': ([0]*75 + [-50]*75),    # 50% штрафов (-50)
#     'D': ([0]*120 + [-125]*30)   # 20% штрафов (-125)
# }

# # Перемешиваем наказания, чтобы распределение стало равномерным
# for deck in IGT_PENALTY_SCHEMES.values():
#     random.shuffle(deck)

# def init_igt_decks():
#     decks = {}
#     for deck, penalties in IGT_PENALTY_SCHEMES.items():
#         decks[deck] = {
#             'penalties': penalties,
#             'index': 0
#         }
#     return decks


def generate_trials(task="cct_hot"):
    if task == "cct_hot":
        # Новая логика для cct_hot
        trials = []
        # Генерируем базовые экспериментальные трейлы
        for lc in FACTORS['loss_cards']:
            for ga in FACTORS['gain_amount']:
                for la in FACTORS['loss_amount']:
                    trial = {
                        'loss_cards': lc,
                        'gain_amount': ga,
                        'loss_amount': la,
                        'trial_type': 'random_loss'  # экспериментальный трейл
                    }
                    trials.append(trial)
        # 27 уникальных комбинаций; умножив на 2, получим 54 экспериментальных трейла
        experimental_trials = trials * 4
        random.shuffle(experimental_trials)
        return experimental_trials
    else:
        # Для cct_cold старая логика: 54 случайных трейла
        trials = []
        for lc in FACTORS['loss_cards']:
            for ga in FACTORS['gain_amount']:
                for la in FACTORS['loss_amount']:
                    trial = {
                        'loss_cards': lc,
                        'gain_amount': ga,
                        'loss_amount': la,
                        'trial_type': 'random_loss'  # здесь все трейлы случайные
                    }
                    trials.append(trial)
        # Предположим, что умножение на 2 даёт 54 уникальных трейла (так было раньше)
        trials = trials * 4
        random.shuffle(trials)
        result_trials = trials * 2
        return result_trials


def mark_task_completed(user_id, task_name):
    device = get_device_type()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO user_progress (user_id, task_name, device_type)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, task_name) DO NOTHING
        """, (user_id, task_name, device))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


@app.route('/mark_instructions_viewed/<task_name>', methods=['POST'])
def mark_instructions_viewed(task_name):
    session[f'{task_name}_instructions_viewed'] = True
    session.modified = True
    return jsonify({'status': 'success'})

@app.route('/task/<task_name>')
def task(task_name):
    valid_tasks = {
        'igt': 'igt.html',
        'bart': 'bart.html',
        'cct_hot': 'cct_hot.html',
        'cct_cold': 'cct_cold.html'
    }

    instructions = {
        'igt': {
            'title': 'Инструкция к заданию',
            'content': '''В этом задании вам надо выбирать одну из четырех карт (A, B, C или D), кликая на неё мышкой.
            В каждой попытке вы можете выиграть какое-то количество денег, но в то же время есть риск получить штраф. После каждого выбора
            вы увидите окно с суммой заработанных или потерянных денег. Вам нужно нажать на кнопку "Следующая попытка" или клавишу "Пробел", чтобы закрыть это окно и
            перейти к следующей попытке. Заработанные деньги будут добавлены в ваш кошелёк "Баланс", а штрафные - будут вычтены.
            В самом начале на вашем балансе будет находиться 2000₽. Всего у вас будет 150 попыток.
            Постарайтесь заработать как можно больше денег за отведенные попытки.'''
        },
        'bart': {
            'title': 'Инструкция к заданию',
            'content': '''Во время этого задания вам будет представлено 50 воздушных шаров, по одному за раз.
            Для каждого воздушного шара вы можете нажать на кнопку с надписью «Надуть»,
            чтобы увеличить его размер. <br>За каждое накачивание вы получите 5 рублей во временном банке. Вам не будет показана сумма,
            накопленная во временном банке. <br>В любой момент вы можете прекратить накачивать воздушный шар и нажать на кнопку с надписью
            «Забрать». Нажатие на эту кнопку переведет вас на следующий воздушный шар и переведет накопленные деньги из вашего временного
            банка в ваш постоянный банк с надписью «Всего заработано». Сумма, которую вы заработали на предыдущем воздушном шаре,
            отображается в поле с надписью «Прошлый шар». <br>Вы сами решаете, насколько сильно накачать воздушный шар, но имейте
            в виду, что в какой-то момент воздушный шар лопнет. Точка взрыва различается для разных воздушных шаров. Чем больше вы надуваете шар, тем выше шанс, что он взорвется. 
            Если шар лопнет до того, как вы нажмете «Забрать», то вы перейдете к следующему шарику, и все деньги в вашем временном банке будут
            потеряны. Взорвавшиеся шарики не влияют на деньги, накопленные в вашем постоянном банке.'''
        },
        'cct_hot': {
            'title': 'Инструкция к заданию',
            'content': '''Перед вами расположено 32 карты: какие-то из них "хорошие" и могут принести вам деньги, а какие-то "плохие", и
            за их выбор предусмотрен штраф. На странице у вас есть информация по текущему раскладу. Карты проигрыша - это количество "плохих" карт
            в раскладе. Награда за карту - это сумма, которую вы можете получить за выбор "хорошей" карты. Размер проигрыша - это штраф, который вы
            можете получить за выбор "плохой" карты (все остальные карты считаются хорошими). Вы можете выбрать столько карт, сколько посчитаете нужным. Как только вы закончите выбирать,
            нажмите на кнопку "Закончить попытку". Это позволит сохранить заработанные за текущую попытку деньги и перейти к новой попытке.
            Имейте в виду, что как только вы выберете "плохую" карту, ваша попытка будет окончена автоматически, все заработанные деньги исчезнут,
            а штраф будет вычтен из заработанных ранее денег.'''
        },
        'cct_cold': {
            'title': 'Инструкция к заданию',
            'content': '''Перед вами расположено 32 карты: какие-то из них "хорошие" и могут принести вам деньги, а какие-то "плохие", и за их
            выбор предусмотрен штраф. Награда за карту - это сумма, которую вы получите за каждую перевернутую «хорошую» карту.
            Размер проигрыша - это штраф, который вы получите, если перевернёте "плохую" карту. Сверху у вас есть информация по текущему раскладу: размер выигрыша за каждую перевернутую
            «хорошую», размер проигрыша за выбор "плохой" карты, а также количество плохих карт в раскладе (все остальные карты считаются хорошими). Вы можете перевернуть столько карт, сколько посчитаете нужным.
            Как только вы определитесь с выбором, вам необходимо нажать на кнопку с числом, соответствующим количеству карт, которое вы решили
            перевернуть. Имейте в виду, что среди выбранных вами карт может оказаться сразу несколько "плохих", и штраф вы получите за каждую из них.
            В игре будет несколько раундов. Вы не получите никакой обратной связи по поводу количества заработанных или потерянных денег до конца игры.
            Однако в некоторых попытках вам будет дана обратная связь по количеству плохих карт среди выбранных вами.
            '''
        }
    }

    if task_name not in session.get('completed_tasks', []):
        # Можно использовать проверку request.referrer для определения, что пользователь пришёл не с той же страницы игры.
        # Например, для BART:
        if task_name == 'bart':
            bart_url = url_for('task', task_name='bart')
            if not (request.referrer and request.referrer.endswith(bart_url)):
            #if (request.referrer):
            #if 'page_loaded_once' in session:
                user_id = session.get('user_id')
                if user_id:
                    conn = get_db()
                    cursor = conn.cursor()
                        # Удаляем все записи для IGT данного пользователя
                    cursor.execute('DELETE FROM bart_results WHERE user_id = %s', (user_id,))
                    conn.commit()
                    cursor.close()
                    # Сброс переменных игры BART
                session.pop('bart_current', None)
                session.pop('bart_total_points', None)
                session.pop('bart_trials', None)
                session.pop(f'{task_name}_instructions_viewed', None)
                    # Инициализация заново
                session['bart_trials'] = 50  # число раундов
                session['bart_current'] = 0
                session['bart_total_points'] = 0

        elif task_name == 'igt':
            igt_url = url_for('task', task_name='igt')
            if not (request.referrer and request.referrer.endswith(igt_url)):
                user_id = session.get('user_id')
                if user_id:
                    conn = get_db()
                    cursor = conn.cursor()
                    # Удаляем все записи для IGT данного пользователя
                    cursor.execute('DELETE FROM igt_results WHERE user_id = %s', (user_id,))
                    conn.commit()
                    cursor.close()
                # Сброс session-переменных (если требуется)
                session.pop(f'{task_name}_instructions_viewed', None)
                session['igt_trials'] = 150
                session['igt_current'] = 0
                session['igt_total_points'] = 2000
                session['igt_decks'] = init_igt_decks()
        elif task_name in ['cct_hot', 'cct_cold']:
            cct_url = url_for('task', task_name=task_name)
            if not (request.referrer and request.referrer.endswith(cct_url)):
                user_id = session.get('user_id')
                if user_id:
                    conn = get_db()
                    cursor = conn.cursor()
                    # Удаляем все записи для IGT данного пользователя
                    cursor.execute(f'DELETE FROM {task_name}_results WHERE user_id = %s', (user_id,))
                    conn.commit()
                    cursor.close()
                session.pop(f'{task_name}_current', None)
                session.pop(f'{task_name}_trials', None)
                session.pop(f'{task_name}_instructions_viewed', None)
                session[f'{task_name}_trials'] = generate_trials(task=task_name)
                session[f'{task_name}_current'] = 0

    if task_name not in session.get('sequence', []):
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 1 FROM user_progress
        WHERE user_id = %s AND task_name = %s
    ''', (session['user_id'], task_name))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard'))
    cursor.close()
    conn.close()

    # Handle IGT task
    if task_name == 'igt':
        # Get actual progress from database
        conn = get_db()
        cursor = conn.cursor()

        # Get current trial number
        cursor.execute('SELECT COUNT(*) FROM igt_results WHERE user_id = %s', (session['user_id'],))
        current_trial = cursor.fetchone()[0]

        # Get total points
        cursor.execute('SELECT SUM(points_earned) FROM igt_results WHERE user_id = %s', (session['user_id'],))
        total_points = 2000 + (cursor.fetchone()[0] or 0)

        cursor.close()
        conn.close()

        # Check if instructions need to be shown
        instruction_key = f'{task_name}_instructions_viewed'
        show_instructions = not session.get(instruction_key, False)

        return render_template(
            'igt.html',
            current_trial=current_trial + 1,  # Display next trial number
            total_trials=150,
            total_points=total_points,
            instruction_title=instructions[task_name]['title'],
            instruction_content=instructions[task_name]['content'],
            show_instructions=show_instructions
        )

    # Handle BART task
    if task_name == 'bart':
        # Initialize session variables if they don't exist
        if 'bart_trials' not in session:
            session['bart_trials'] = 50 
        if 'bart_current' not in session:
            session['bart_current'] = 0
        if 'bart_total_points' not in session:
            session['bart_total_points'] = 0
        # при старте BART
        
        if 'bart_break_points' not in session:
            points = list(range(3, 65))   # 1..64
            random.shuffle(points)
            session['bart_break_points'] = points[:50]  # ровно 50 trial

        # After committing the insert
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT points_earned
            FROM bart_results
            WHERE user_id = %s
            ORDER BY result_id DESC
            LIMIT 1
        ''', (session['user_id'],))

        last_points = cursor.fetchone()
        if last_points:
            last_points_earned = last_points[0]
        else:
            last_points_earned = 0  # Default value if no records found

        cursor.close()
        conn.close()

        # Check if all trials are completed
        if session.get('bart_current', 0) >= session.get('bart_trials', 0):
            # Mark the task as completed
            if 'completed_tasks' not in session:
                session['completed_tasks'] = []
            session['completed_tasks'].append('bart')
            session.modified = True

            # Redirect to the next task or dashboard
            sequence = session.get('sequence', [])
            try:
                current_idx = sequence.index(task_name)
                next_task = sequence[current_idx + 1]
                return redirect(url_for('task', task_name=next_task))
            except (ValueError, IndexError):
                return redirect(url_for('dashboard'))

        explosion_point = session['bart_break_points'][session['bart_current']]
        session['bart_break_point'] = explosion_point


        # Check if instructions need to be shown
        instruction_key = f'{task_name}_instructions_viewed'
        show_instructions = not session.get(instruction_key, False)

        # Render the BART template
        return render_template(
            valid_tasks[task_name],
            trial_number=session['bart_current'] + 1,
            total_trials=session['bart_trials'],
            total_points=session['bart_total_points'],
            explosion_point=explosion_point,
            instruction_title=instructions[task_name]['title'],
            instruction_content=instructions[task_name]['content'],
            show_instructions=show_instructions,
            points_earned=last_points_earned
        )

    # Initialize task-specific session variables
    if task_name in ['cct_hot', 'cct_cold']:
        if f'{task_name}_trials' not in session:
            session[f'{task_name}_trials'] = generate_trials(task=task_name)
        if f'{task_name}_current' not in session:
            session[f'{task_name}_current'] = 0

        current_trial = session[f'{task_name}_trials'][session[f'{task_name}_current']]
        loss_cards = current_trial['loss_cards']
        gain_amount = current_trial['gain_amount']
        loss_amount = current_trial['loss_amount']
        trial_number = session[f'{task_name}_current'] + 1
        trial_type = current_trial.get('trial_type', 'random_loss')
        total_trials = len(session[f'{task_name}_trials'])  # will be 63

        instruction_key = f'{task_name}_instructions_viewed'
        show_instructions = not session.get(instruction_key, False)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT task1, task2, task3, task4, feedback_type
            FROM user_sequences
            WHERE user_id = %s
        """, (session['user_id'],))
        seq_row = cursor.fetchone()
        cursor.close()
        conn.close()

        return render_template(
            valid_tasks[task_name],
            loss_cards=loss_cards,
            gain_amount=gain_amount,
            loss_amount=loss_amount,
            trial_number=f"{trial_number}/{total_trials}",
            instruction_title=instructions[task_name]['title'],
            instruction_content=instructions[task_name]['content'],
            show_instructions=show_instructions,
            trial_type=trial_type,
            feedback_type=seq_row[-1]
        )

    # Render appropriate template for other tasks
    return render_template(valid_tasks[task_name])

@app.route('/save_cct_hot', methods=['POST'])
def save_cct_hot():
    data = request.get_json()
    user_id = session.get('user_id')

    current_trial = session['cct_hot_trials'][session['cct_hot_current']]

    trial_number = data['trialNumber']
    trial_type = current_trial.get('trial_type', 'experimental')

    decision = data['decision']
    result = data.get('result')          # win / loss / None
    flip_number = data['flip_number']

    current_points = data['current_points']

    loss_cards = current_trial['loss_cards']
    gain_amount = current_trial['gain_amount']
    loss_amount = current_trial['loss_amount']

    # Итоговые очки за trial фиксируем ТОЛЬКО при stop или loss
    if decision == 0 or result == 'loss':
        points = current_points
    else:
        points = 0   # временно, будет обновлено позже

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO cct_hot_results (
            user_id,
            trial_number,
            trial_type,
            decision,
            result,
            flip_number,
            current_points,
            points,
            reaction_time,
            loss_cards,
            gain_amount,
            loss_amount
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        user_id,
        trial_number,
        trial_type,
        decision,
        result,
        flip_number,
        current_points,
        points,
        data.get('reaction_time'),
        loss_cards,
        gain_amount,
        loss_amount
    ))

    conn.commit()
    cursor.close()
    conn.close()

    # Переход к следующему trial
    if decision == 0 or result == 'loss':
        session['cct_hot_current'] += 1

    is_final_trial = session['cct_hot_current'] >= len(session['cct_hot_trials'])

    if is_final_trial:
        mark_task_completed(user_id, 'cct_hot')
        session.setdefault('completed_tasks', []).append('cct_hot')

    return jsonify({
        'status': 'completed' if is_final_trial else 'success',
        'redirect_url': url_for('intermediate', task_name='cct_hot') if is_final_trial else None
    })


@app.route('/save_cct_cold', methods=['POST'])
def save_cct_cold():
    data = request.get_json()
    user_id = session.get('user_id')
    task_name = 'cct_cold'

     # Initialize if missing
    if f'{task_name}_current' not in session:
        session[f'{task_name}_current'] = 0
    if f'{task_name}_trials' not in session:
        session[f'{task_name}_trials'] = generate_trials(task=task_name)

    # Get the current trial data
    current_trial = session['cct_cold_trials'][session['cct_cold_current']]
    loss_cards = current_trial['loss_cards']
    gain_amount = current_trial['gain_amount']
    loss_amount = current_trial['loss_amount']
    num_cards = data['numCards']

    # Симуляция выбора карт
    loss_encountered = False
    if num_cards > 0:
        # Создаем колоду: 1 - плохая карта, 0 - хорошая
        deck = [1] * loss_cards + [0] * (32 - loss_cards)
        random.shuffle(deck)
        # Проверяем, есть ли плохие карты среди выбранных
        selected_cards = deck[:num_cards]
        loss_encountered = 1 in selected_cards
        loss_cards_selected = selected_cards.count(1)
    elif num_cards == 0:
        loss_encountered = False
        loss_cards_selected = 0
    # Рассчитываем очки
    if loss_encountered:
        if 32 - num_cards < loss_cards:
            points_earned = -loss_amount*loss_cards_selected
        else:
            points_earned = -loss_amount
    else:
        points_earned = num_cards * gain_amount

    # Save results to database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cct_cold_results (user_id, trial_number, num_cards, loss_encountered, points_earned, reaction_time, loss_cards, gain_amount, loss_amount)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (user_id, data['trialNumber'], num_cards, loss_encountered, points_earned, data['reaction_time'], loss_cards, gain_amount, loss_amount))
    conn.commit()
    cursor.close()
    conn.close()

    # Update trial counter
    session['cct_cold_current'] += 1

    # Check if final trial
    is_final_trial = session['cct_cold_current'] >= len(session['cct_cold_trials'])

        # После сохранения данных
    if is_final_trial:
        mark_task_completed(user_id, 'cct_cold')
        if 'completed_tasks' not in session:
            session['completed_tasks'] = []
        if 'cct_cold' not in session['completed_tasks']:
            session['completed_tasks'].append('cct_cold')

    return jsonify({
        'status': 'completed' if is_final_trial else 'success',
        'redirect_url': url_for('intermediate', task_name='cct_cold') if is_final_trial else None,
        'bad_cards_selected': loss_cards_selected,  # Возвращаем количество плохих карт
        'loss_encountered': loss_encountered  # Возврат флага, были ли потери
    })

@app.route('/save_igt', methods=['POST'])
def save_igt():
    data = request.get_json()
    user_id = session.get('user_id')
    task_name = 'igt'

    #Initialize session variables
    session.setdefault('igt_trials', 150)
    session.setdefault('igt_current', 0)
    session.setdefault('igt_total_points', 2000)
    if 'igt_decks' not in session:
        session['igt_decks'] = init_igt_decks()

     # Initialize if missing
    if f'{task_name}_current' not in session:
        session[f'{task_name}_current'] = 0
    if f'{task_name}_trials' not in session:
        session[f'{task_name}_trials'] = generate_trials()

    # Get selected deck from client
    selected_deck = data['deck']

    payout = IGT_PAYOUTS[selected_deck]

    deck_state = session['igt_decks'][selected_deck]

    # Берём штраф из текущего блока
    penalty = deck_state['block'][deck_state['index']]
    points_earned = payout + penalty  # penalty уже отрицательный

    # Сдвигаем индекс
    deck_state['index'] += 1

    # Если блок закончился — создаём новый
    if deck_state['index'] >= 10:
        # Обновляем только текущую колоду
        new_block = IGT_PENALTY_SCHEMES[selected_deck].copy()
        random.shuffle(new_block)
        deck_state['block'] = new_block
        deck_state['index'] = 0

    # Update session variables
    session['igt_total_points'] += points_earned
    session['igt_current'] += 1
    session.modified = True

    # Save results to database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO igt_results (user_id, trial_number, deck, payout, penalty, points_earned, reaction_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (user_id, session['igt_current'], selected_deck, payout, penalty, points_earned, data['reaction_time']))
    conn.commit()
    cursor.close()
    conn.close()

    # Check if final trial
    is_final_trial = session['igt_current'] >= session['igt_trials']

        # После сохранения данных
    if is_final_trial:
        mark_task_completed(user_id, 'igt')
        if 'completed_tasks' not in session:
            session['completed_tasks'] = []
        if 'igt' not in session['completed_tasks']:
            session['completed_tasks'].append('igt')

    return jsonify({
        'status': 'completed' if is_final_trial else 'success',
        'payout': payout,
        'penalty': penalty,
        'points_earned': points_earned,
        'new_total_points': session['igt_total_points'],
        'new_trial_number': session['igt_current'],
        'redirect_url': url_for('intermediate', task_name='igt') if is_final_trial else None
    })


@app.route('/next_trial/<task_name>')
def next_trial(task_name):
    # Initialize completed tasks list
    if 'completed_tasks' not in session:
        session['completed_tasks'] = []

    # Get task sequence
    sequence = session.get('sequence', [])

    # Handle BART
    if task_name == 'bart':
        # Increment trial counter
        session['bart_current'] = session.get('bart_current', 0) + 1
        session.modified = True

        # Check completion after increment
        if session['bart_current'] >= session.get('bart_trials', 0):
            if 'bart' not in session['completed_tasks']:
                session['completed_tasks'].append('bart')
            return redirect(url_for('intermediate', task_name=task_name))
        return redirect(url_for('task', task_name=task_name))

    # Handle IGT
    elif task_name == 'igt':

        session.modified = True

        if session['igt_current'] >= session.get('igt_trials', 150):
            return redirect(url_for('intermediate', task_name='igt'))
        return redirect(url_for('task', task_name='igt'))


    # Handle CCT tasks
    elif task_name in ['cct_hot', 'cct_cold']:
        # Increment trial counter

        session.modified = True

        # Check completion after increment
        if session[f'{task_name}_current'] >= len(session.get(f'{task_name}_trials', [])):
            if task_name not in session['completed_tasks']:
                session['completed_tasks'].append(task_name)
            return redirect(url_for('intermediate', task_name=task_name))
        return redirect(url_for('task', task_name=task_name))

    return redirect(url_for('dashboard'))

@app.route('/save_bart', methods=['POST'])
def save_bart():
    data = request.get_json()
    user_id = session['user_id']

    trial_number = data['trialNumber']
    pump_number = data['pumpNumber']
    #break_point = data['breakPoint']
    break_point = session['bart_break_point']
    reaction_time = data['reaction_time']

    popped = pump_number == break_point

    # points внутри trial
    if popped:
        points_earned = 0
        trial_points = 0
    else:
        trial_points = pump_number * 5
        points_earned = trial_points

    # total_points обновляется ТОЛЬКО после завершения trial
    total_points = session.get('bart_total_points', 0)

    if data.get('trialEnded', False):
        if not popped:
            total_points += trial_points
        session['bart_total_points'] = total_points
        session['bart_current'] += 1
    # Проверка, является ли это последним trial
    is_final_trial = session['bart_current'] >= session.get('bart_trials', 50)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bart_results (
            user_id, trial_number, pump_number,
            break_point, popped,
            points_earned, total_points, reaction_time
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        user_id, trial_number, pump_number,
        break_point, popped,
        points_earned, total_points, reaction_time
    ))
    conn.commit()
    cursor.close()
    conn.close()

    session['bart_current'] = trial_number
    session['bart_total_points'] = total_points
    session['bart_last_points'] = points_earned

    # Если это последний trial, пометь задание как выполненное
    if is_final_trial:
        mark_task_completed(user_id, 'bart')
        if 'completed_tasks' not in session:
            session['completed_tasks'] = []
        if 'bart' not in session['completed_tasks']:
            session['completed_tasks'].append('bart')

    return jsonify({
        'status': 'ok', 
        'total_points': total_points,
        'redirect_url': url_for('intermediate', task_name='bart') if is_final_trial else None,
        'new_break_point': session['bart_break_points'][session['bart_current']] if not is_final_trial else None})


@app.route('/intermediate/<task_name>', methods=['GET', 'POST'])
def intermediate(task_name):
    # Verify task is in sequence
    if task_name not in session.get('sequence', []):
        return redirect(url_for('dashboard'))

    # Verify task completion
    is_completed = False
    if task_name == 'bart':
        is_completed = session.get('bart_current', 0) >= session.get('bart_trials', 0)
    elif task_name == 'igt':
        is_completed = session.get('igt_current', 0) >= session.get('igt_trials', 0)
    elif task_name in ['cct_hot', 'cct_cold']:
        is_completed = session.get(f'{task_name}_current', 0) >= len(session.get(f'{task_name}_trials', []))

    if not is_completed:
        return redirect(url_for('task', task_name=task_name))

    # Mark task as completed
    if 'completed_tasks' not in session:
        session['completed_tasks'] = []
    if task_name not in session['completed_tasks']:
        session['completed_tasks'].append(task_name)
        session.modified = True

    # Get next task
    sequence = session.get('sequence', [])
    try:
        current_idx = sequence.index(task_name)
        next_task = sequence[current_idx + 1]
    except (ValueError, IndexError):
        next_task = None

    # Получение суммы заработка
    total_money = 0
    if task_name == 'igt':
        total_money = session.get('igt_total_points', 0)
    elif task_name == 'bart':
        total_money = session.get('bart_total_points', 0)
    elif task_name in ['cct_hot', 'cct_cold']:
        conn = get_db()
        cursor = conn.cursor()
        if task_name == "cct_hot":
            cursor.execute(f'SELECT SUM(points) FROM {task_name}_results WHERE user_id = %s',
                          (session['user_id'],))
        elif task_name == "cct_cold":
            cursor.execute(f'SELECT SUM(points_earned) FROM {task_name}_results WHERE user_id = %s',
                          (session['user_id'],))
        total_money = cursor.fetchone()[0] or 0
        cursor.close()
        conn.close()
    # Проверка, проходили ли анкету ранее
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*)
        FROM tasks_questions
        WHERE user_id = %s AND task_name = %s
    ''', (session['user_id'], task_name))
    survey_exists = cursor.fetchone()[0] > 0
    passed_survey = bool(survey_exists)
    cursor.close()
    conn.close()

    # Обрабатываем POST-запрос
    if request.method == 'POST':
        # Сохраняем ответы в базу данных
        conn = get_db()
        cursor = conn.cursor()

        # Ответы на вопросы зависят от конкретного задания
        if task_name == 'igt':
            q1_answer = request.form.get('i1')
            q2_answers = ', '.join(request.form.getlist('i2[]'))  # Используем request.form.getlist()
            q3_answer = request.form.get('i3')

            cursor.execute('''
                INSERT INTO tasks_questions (user_id, task_name, question, answer)
                VALUES (%s, %s, %s, %s)
            ''', (session['user_id'], task_name, 'i1', q1_answer))
            cursor.execute('''
                INSERT INTO tasks_questions (user_id, task_name, question, answer)
                VALUES (%s, %s, %s, %s)
            ''', (session['user_id'], task_name, 'i2', q2_answers))
            cursor.execute('''
                INSERT INTO tasks_questions (user_id, task_name, question, answer)
                VALUES (%s, %s, %s, %s)
            ''', (session['user_id'], task_name, 'i3', q3_answer))

        elif task_name == 'bart':
            q1_answer = request.form.get('b1')
            q2_answer = request.form.get('b2')

            cursor.execute('''
                INSERT INTO tasks_questions (user_id, task_name, question, answer)
                VALUES (%s, %s, %s, %s)
            ''', (session['user_id'], task_name, 'b1', q1_answer))
            cursor.execute('''
                INSERT INTO tasks_questions (user_id, task_name, question, answer)
                VALUES (%s, %s, %s, %s)
            ''', (session['user_id'], task_name, 'b2', q2_answer))

        conn.commit()
        cursor.close()
        return redirect(url_for('intermediate', task_name=task_name))

    return render_template('intermediate.html',
                         task_name=task_name,
                         next_task=next_task,
                         total_money=total_money,
                         passed_survey=passed_survey)

def get_user_results(user_id):
    conn = get_db()
    cursor = conn.cursor()
    results = {}
    total_earnings = 0

    # Пример для IGT
    cursor.execute('SELECT SUM(points_earned) FROM igt_results WHERE user_id = %s', (user_id,))
    igt_total = cursor.fetchone()[0] or 0
    results['Выбор одной карты из четырёх'] = 2000 + igt_total
    total_earnings += (2000 + igt_total)

    # Пример для BART
    cursor.execute('SELECT total_points FROM bart_results WHERE user_id = %s ORDER BY result_id DESC LIMIT 1', (user_id,))
    # bart_total = cursor.fetchone()[0] or 0
    result = cursor.fetchone()
    if result is None:
        bart_total = 0
    else:
        bart_total = result[0]
    results['Надуть шарик'] = bart_total
    total_earnings += bart_total

    # Пример для CCT-hot
    cursor.execute('SELECT SUM(points) FROM cct_hot_results WHERE user_id = %s', (user_id,))
    cct_hot_total = cursor.fetchone()[0] or 0
    results['Выбрать N карт последовательно'] = cct_hot_total
    total_earnings += cct_hot_total

    # Пример для CCT-cold
    cursor.execute('SELECT SUM(points_earned) FROM cct_cold_results WHERE user_id = %s', (user_id,))
    cct_cold_total = cursor.fetchone()[0] or 0
    results['Выбрать N карт одновременно'] = cct_cold_total
    total_earnings += cct_cold_total

    cursor.close()
    conn.close()
    return results, total_earnings

@app.route('/results')
def results():
    user_id = session.get('user_id')
    if not user_id:
        flash("Пожалуйста, войдите в систему.", "warning")
        return redirect(url_for('login'))

    # Проверяем, хотя бы одну игру закончили?
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM user_progress WHERE user_id = %s', (user_id,))
    completed = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    if completed == 0:
        flash("Результаты появятся после завершения всех игры.", "info")
        return redirect(url_for('dashboard'))

    # Считаем все метрики
    questionnaire = get_questionnaire_results(user_id)
    bart          = get_bart_metrics(user_id)
    igt           = get_igt_metrics(user_id)
    cct_hot       = get_cct_hot_metrics(user_id)
    cct_cold      = get_cct_cold_metrics(user_id)
    rfq           = get_rfq_results(user_id)

    return render_template(
        'results.html',
        questionnaire=questionnaire,
        bart=bart,
        igt=igt,
        cct_hot=cct_hot,
        cct_cold=cct_cold,
        rfq=rfq
    )

@app.route('/test')
def test():
    return render_template("test.html")


# def get_questionnaire_results(user_id):
#     conn = get_db()
#     cursor = conn.cursor()

#     # Получаем все ответы
#     cursor.execute('SELECT question_number, response FROM questionnaire_responses WHERE user_id = %s', (user_id,))
#     responses = cursor.fetchall()

#     # Вопросы, требующие обратного кодирования
#     reverse_scored = {4, 5, 13, 14, 15, 16, 17, 19, 20, 21, 26}
#     total_score = 0

#     for row in responses:
#         qnum, response = row['question_number'], row['response']
#         if qnum in reverse_scored:
#             response = 5 - response  # обратное кодирование
#         total_score += response

#     # Процентиль среди всех участников
#     cursor.execute('SELECT user_id FROM questionnaire_responses GROUP BY user_id')
#     all_user_ids = [row['user_id'] for row in cursor.fetchall()]

#     scores = []
#     for uid in all_user_ids:
#         cursor.execute('SELECT question_number, response FROM questionnaire_responses WHERE user_id = %s', (uid,))
#         user_responses = cursor.fetchall()
#         user_score = 0
#         for row in user_responses:
#             qnum, response = row['question_number'], row['response']
#             if qnum in reverse_scored:
#                 response = 5 - response
#             user_score += response
#         scores.append(user_score)

#     scores.sort()
#     if scores:
#         rank = scores.index(total_score) + 1
#         percentile = round(100 * rank / len(scores), 1)
#     else:
#         percentile = 0.0
#     cursor.close()
#     conn.close()
#     return {
#         'total_score': total_score,
#         'percentile': percentile
#     }

def get_questionnaire_results(user_id):
    conn = get_db()
    cursor = conn.cursor()

    # Получаем все ответы
    cursor.execute('SELECT question_number, response FROM questionnaire_responses WHERE user_id = %s', (user_id,))
    responses = cursor.fetchall()

    # Вопросы, требующие обратного кодирования
    reverse_scored = {4, 5, 13, 14, 15, 16, 17, 19, 20, 21, 26}
    total_score = 0

    for row in responses:
        qnum, response = row[0], row[1]  # Доступ по индексам
        if qnum in reverse_scored:
            response = 5 - response  # Обратное кодирование
        total_score += response

    # Процентиль среди всех участников
    cursor.execute('SELECT user_id FROM questionnaire_responses GROUP BY user_id')
    all_user_ids = [row[0] for row in cursor.fetchall()]  # Доступ по индексам

    scores = []
    for uid in all_user_ids:
        cursor.execute('SELECT question_number, response FROM questionnaire_responses WHERE user_id = %s', (uid,))
        user_responses = cursor.fetchall()
        user_score = 0
        for row in user_responses:
            qnum, response = row[0], row[1]  # Доступ по индексам
            if qnum in reverse_scored:
                response = 5 - response
            user_score += response
        scores.append(user_score)

    scores.sort()
    if scores:
        rank = scores.index(total_score) + 1
        percentile = round(100 * rank / len(scores), 1)
    else:
        percentile = 0.0
    cursor.close()
    conn.close()
    return {
        'total_score': total_score,
        'percentile': percentile
    }


def get_bart_metrics(user_id):
    conn = get_db()
    cursor = conn.cursor()

    # Индивидуальные показатели
    cursor.execute('''
        WITH TrialSummary AS (
            SELECT
                trial_number,
                MAX(pump_number) AS max_pumps_in_trial,
                MAX(CAST(popped AS INTEGER)) AS exploded
            FROM bart_results
            WHERE user_id = %s
            GROUP BY trial_number
        )
        SELECT
            AVG(max_pumps_in_trial) AS avg_pumps_per_trial,
            AVG(exploded::FLOAT) AS explosion_rate
        FROM TrialSummary
    ''', (user_id,))
    
    rows = cursor.fetchall()

    # Обработка полученных данных
    avg_pumps = rows[0][0] if rows else 0.0
    explosion_rate = rows[0][1] if rows else 0.0

    # Последний результат по очкам
    cursor.execute('''
        SELECT total_points 
        FROM bart_results 
        WHERE user_id = %s 
        ORDER BY result_id DESC LIMIT 1
    ''', (user_id,))
    total_earn_row = cursor.fetchone()
    total_earn = total_earn_row[0] if total_earn_row else 0

    # Групповые средние
    cursor.execute('''
        WITH GroupTrialSummary AS (
            SELECT
                trial_number,
                MAX(pump_number) AS max_pumps_in_trial,
                MAX(CAST(popped AS INTEGER)) AS exploded
            FROM bart_results
            GROUP BY trial_number
        )
        SELECT
            AVG(max_pumps_in_trial) AS avg_pumps_per_trial,
            AVG(exploded::FLOAT) AS explosion_rate
        FROM GroupTrialSummary
    ''')
    grp_rows = cursor.fetchall()
    grp_avg_pumps = grp_rows[0][0] if grp_rows else 0.0
    grp_explosion = grp_rows[0][1] if grp_rows else 0.0

    # Средняя прибыль по всей группе участников
    cursor.execute('SELECT AVG(total_points) FROM bart_results')
    grp_avg_earn = cursor.fetchone()[0] or 0.0

    cursor.close()
    conn.close()

    # Рассчёт процентов относительно средней группы
    pct_pumps = round(100 * (avg_pumps / grp_avg_pumps - 1), 1) if grp_avg_pumps > 0 else 0.0
    pct_earn = round(100 * (total_earn / grp_avg_earn - 1), 1) if grp_avg_earn > 0 else 0.0
    pct_explosion = round(100 * (explosion_rate / grp_explosion - 1), 1) if grp_explosion > 0 else 0.0

    return {
        'avg_pumps': round(avg_pumps, 1),
        'explosion_rate': round(explosion_rate * 100, 1),
        'total_earn': total_earn,
        'pct_pumps': pct_pumps,
        'pct_earn': pct_earn,
        'pct_explosion': pct_explosion
    }


def get_igt_metrics(user_id):
    conn = get_db()
    cursor = conn.cursor()

    # Сумма и среднее
    cursor.execute('''
        SELECT
            SUM(points_earned)  AS total_net,
            AVG(points_earned)  AS avg_net
        FROM igt_results
        WHERE user_id = %s
    ''', (user_id,))
    row = cursor.fetchone()
    total_net = row[0] or 0  # Доступ по индексу
    avg_net   = row[1] or 0.0

    # Доля выгодных выборов (колоды C или D)
    cursor.execute('''
        SELECT COUNT(*) * 1.0 / (
            SELECT COUNT(*) FROM igt_results WHERE user_id = %s
        ) AS pct_good
        FROM igt_results
        WHERE user_id = %s AND deck IN ('C','D')
    ''', (user_id, user_id))
    pct_good = round(100 * (cursor.fetchone()[0] or 0.0), 1)

    # Процентиль по total_net
    cursor.execute('''
        SELECT SUM(points_earned) AS sum_net
        FROM igt_results
        GROUP BY user_id
    ''')
    all_nets = sorted([r[0] for r in cursor.fetchall()])  # Доступ по индексу
    if all_nets:
        rank = all_nets.index(total_net) + 1
        pct_net = round(100 * rank / len(all_nets), 1)
    else:
        pct_net = 0.0

    cursor.close()
    conn.close()
    return {
        'total_net': 2000 + total_net,
        'avg_net': round(avg_net, 1),
        'pct_good': pct_good,
        'pct_net': pct_net
    }

#
# 4) Метрики для CCT-hot и CCT-cold
#
# def get_cct_hot_metrics(user_id):
#     """Метрики для CCT-hot: flipped_cards и points"""
#     conn = get_db()
#     cursor = conn.cursor()

#     # Пользовательские метрики (только experimental trials)
#     cursor.execute('''
#         SELECT
#             AVG(flip_number)    AS avg_flip,
#             AVG(points)           AS avg_pts
#         FROM cct_hot_results
#         WHERE user_id = %s AND trial_type = 'experimental'
#     ''', (user_id,))
#     row = cursor.fetchone()
#     avg_flip = row['avg_flip'] or 0.0
#     avg_pts  = row['avg_pts']  or 0.0

#     # Групповые средние
#     cursor.execute('''
#         SELECT
#             AVG(flip_number),
#             AVG(points)
#         FROM cct_hot_results
#         WHERE trial_type = 'experimental'
#     ''')
#     grp = cursor.fetchone()
#     grp_flip = grp[0] or 1.0
#     grp_pts  = grp[1] or 1.0
#     cursor.close()
#     conn.close()

#     return {
#         'avg_flip': round(avg_flip,1),
#         'avg_pts':  round(avg_pts,1),
#         'pct_flip': round(100*(avg_flip/grp_flip - 1),1),
#         'pct_pts':  round(100*(avg_pts/grp_pts   - 1),1)
#     }

def get_cct_hot_metrics(user_id):
    """Метрики для CCT-hot: flip_number и points"""
    conn = get_db()
    cursor = conn.cursor()

    # Пользовательские метрики (только experimental trials)
    cursor.execute('''
        SELECT
            AVG(flip_number)    AS avg_flip,
            AVG(points)           AS avg_pts
        FROM cct_hot_results
        WHERE user_id = %s
    ''', (user_id,))
    row = cursor.fetchone()
    avg_flip = row[0] or 0.0  # Доступ по индексу
    avg_pts  = row[1] or 0.0

    # Групповые средние
    cursor.execute('''
        SELECT
            AVG(flip_number),
            AVG(points)
        FROM cct_hot_results
    ''')
    grp = cursor.fetchone()
    grp_flip = grp[0] or 1.0
    grp_pts  = grp[1] or 1.0
    cursor.close()
    conn.close()

    return {
        'avg_flip': round(avg_flip,1),
        'avg_pts':  round(avg_pts,1),
        'pct_flip': round(100*(avg_flip/grp_flip - 1),1),
        'pct_pts':  round(100*(avg_pts/grp_pts   - 1),1)
    }


# def get_cct_cold_metrics(user_id):
#     """Метрики для CCT-cold: num_cards и points_earned"""
#     conn = get_db()
#     cursor = conn.cursor()

#     # Пользовательские метрики (всех trials)
#     cursor.execute('''
#         SELECT
#             AVG(num_cards)        AS avg_num,
#             AVG(points_earned)    AS avg_pts
#         FROM cct_cold_results
#         WHERE user_id = %s
#     ''', (user_id,))
#     row = cursor.fetchone()
#     avg_num = row['avg_num'] or 0.0
#     avg_pts = row['avg_pts'] or 0.0

#     # Групповые средние
#     cursor.execute('''
#         SELECT
#             AVG(num_cards),
#             AVG(points_earned)
#         FROM cct_cold_results
#     ''')
#     grp = cursor.fetchone()
#     grp_num = grp[0] or 1.0
#     grp_pts = grp[1] or 1.0
#     cursor.close()
#     conn.close()

#     return {
#         'avg_num': round(avg_num,1),
#         'avg_pts': round(avg_pts,1),
#         'pct_num': round(100*(avg_num/grp_num - 1),1),
#         'pct_pts': round(100*(avg_pts/grp_pts - 1),1)
#     }

def get_cct_cold_metrics(user_id):
    """Метрики для CCT-cold: num_cards и points_earned"""
    conn = get_db()
    cursor = conn.cursor()

    # Пользовательские метрики (всех trials)
    cursor.execute('''
        SELECT
            AVG(num_cards)        AS avg_num,
            AVG(points_earned)    AS avg_pts
        FROM cct_cold_results
        WHERE user_id = %s
    ''', (user_id,))
    row = cursor.fetchone()
    avg_num = row[0] or 0.0  # Доступ по индексу
    avg_pts = row[1] or 0.0

    # Групповые средние
    cursor.execute('''
        SELECT
            AVG(num_cards),
            AVG(points_earned)
        FROM cct_cold_results
    ''')
    grp = cursor.fetchone()
    grp_num = grp[0] or 1.0
    grp_pts = grp[1] or 1.0
    cursor.close()
    conn.close()

    return {
        'avg_num': round(avg_num,1),
        'avg_pts': round(avg_pts,1),
        'pct_num': round(100*(avg_num/grp_num - 1),1),
        'pct_pts': round(100*(avg_pts/grp_pts - 1),1)
    }

def get_rfq_results(user_id):
    conn = get_db()
    cursor = conn.cursor()

    # Получаем все ответы пользователя
    cursor.execute('SELECT question_number, response FROM rfq_responses WHERE user_id = %s', (user_id,))
    responses = cursor.fetchall()

    # Создаем словарь ответов для быстрого доступа
    answers = {}
    for row in responses:
        question_num, answer_value = row
        answers[int(question_num)] = int(answer_value)

    # Формула подсчета очков для обеих шкал
    promotion_questions = [1, 3, 7, 9, 10, 11]
    prevention_questions = [2, 4, 5, 6, 8]

    def calculate_subscale_sum(questions, answers, reverse=None):
        """Подсчет суммы очков по списку вопросов"""
        score = 0
        for qn in questions:
            value = answers[qn]
            if reverse and qn in reverse:
                value = 6 - value  # Инвертированное кодирование
            score += value
        return score

    # Подсчет общего балла по обеим шкалам
    raw_promotion_score = calculate_subscale_sum(promotion_questions, answers, reverse={9, 11})
    raw_prevention_score = calculate_subscale_sum(prevention_questions, answers, reverse={2, 4, 6, 8})

    # Получаем общий список всех участников
    cursor.execute('SELECT DISTINCT user_id FROM rfq_responses')
    all_users = [row[0] for row in cursor.fetchall()]

    # Сбор статистики по каждому участнику
    users_scores = {"promotion": [], "prevention": []}
    for uid in all_users:
        cursor.execute('SELECT question_number, response FROM rfq_responses WHERE user_id = %s', (uid,))
        resp = cursor.fetchall()
        answ = {qn: val for qn, val in resp}
        promo_score = calculate_subscale_sum(promotion_questions, reverse={9, 11}, answers=answ)
        prev_score = calculate_subscale_sum(prevention_questions, reverse={2, 4, 6, 8}, answers=answ)
        users_scores["promotion"].append(promo_score)
        users_scores["prevention"].append(prev_score)

    # Рассчитываем процентили
    users_scores["promotion"].sort()
    users_scores["prevention"].sort()

    promotion_rank = users_scores["promotion"].index(raw_promotion_score) + 1
    prevention_rank = users_scores["prevention"].index(raw_prevention_score) + 1

    promotion_percentile = round(100 * promotion_rank / len(users_scores["promotion"]), 1)
    prevention_percentile = round(100 * prevention_rank / len(users_scores["prevention"]), 1)

    cursor.close()
    conn.close()
    return {
        'raw_promotion_score': raw_promotion_score,
        'raw_prevention_score': raw_prevention_score,
        'promotion_percentile': promotion_percentile,
        'prevention_percentile': prevention_percentile
    }

@app.route('/logout')
def logout():
    # Clear all instruction flags
    for key in list(session.keys()):
        if key.endswith('_instructions_viewed'):
            session.pop(key)
    # Clear the session data
    session.clear()

    # Redirect to the main page (home)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
