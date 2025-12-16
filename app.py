from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3, random, json
from itertools import permutations

app = Flask(__name__)
app.secret_key = '#'

# Initialize database and create tables
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Create users table
    # cursor.execute('''
    #     CREATE TABLE IF NOT EXISTS users (
    #         user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         username TEXT UNIQUE NOT NULL,
    #         password_hash TEXT NOT NULL,
    #         age INTEGER,
    #         gender TEXT,
    #         education TEXT
    #     )
    # ''')

    # # Create sequences table
    # cursor.execute('''
    #     CREATE TABLE IF NOT EXISTS sequences (
    #         sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         task1 TEXT NOT NULL,
    #         task2 TEXT NOT NULL,
    #         task3 TEXT NOT NULL,
    #         task4 TEXT NOT NULL,
    #         assigned_count INTEGER DEFAULT 0
    #     )
    # ''')

    # cursor.execute('''
    #     CREATE TABLE IF NOT EXISTS user_progress (
    #         user_id INTEGER NOT NULL,
    #         task_name TEXT NOT NULL,
    #         completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #         PRIMARY KEY (user_id, task_name),
    #         FOREIGN KEY (user_id) REFERENCES users(user_id)
    #     )
    # ''')

    # Populate sequences table
    methods = ["igt", "bart", "cct_hot", "cct_cold"]  # Use endpoint names
    all_sequences = list({p for p in permutations(methods)})  # Get unique permutations
    for seq in all_sequences[:16]:  # Use first 16 unique sequences
        cursor.execute('''
            INSERT OR IGNORE INTO sequences (task1, task2, task3, task4)
            VALUES (?, ?, ?, ?)
        ''', seq)

    conn.commit()
    conn.close()

init_db()

@app.before_request
def check_session():
    if 'user_id' not in session:
        session['user_id'] = None
    if 'completed_tasks' not in session:
        session['completed_tasks'] = []
    if 'sequence' not in session:
        session['sequence'] = []

# Helper function to get database connection
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

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
        age = request.form['age']
        gender = request.form['gender']
        education = request.form['education']
        # Hash the password (use a library like bcrypt in production)
        password_hash = password  # Replace with actual hashing
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, age, gender, education)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, age, gender, education))
            conn.commit()
            flash('Registration successful! Please log in.')
            print('Success!')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another.')
            print('Username already exists.')
        finally:
            conn.close()
    print('Oops.')
    return render_template('register.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        if user and user[1] == password: #here should be password verification
            session['user_id'] = user[0]
            # Load completed tasks from database
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT task_name FROM user_progress WHERE user_id = ?', (user[0],))
            completed_tasks = [row[0] for row in cursor.fetchall()]
            session['completed_tasks'] = completed_tasks
            conn.close()
            flash('Login successfull!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username of password.')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # Get user's progress data
    completed_tasks = []
    task_names = {
        'igt': 'Выбор одной карты из четырёх',
        'bart': 'Надуть шарик',
        'cct_hot': 'Выбрать N карт последовательно',
        'cct_cold': 'Выбрать N карт одновременно'
    }

    # Get the next sequence in round-robin order
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_sequences WHERE user_id = ?', (user_id,))
    existing_sequence = cursor.fetchone()

    if not existing_sequence:
        cursor.execute('SELECT * FROM sequences ORDER BY assigned_count ASC, sequence_id ASC LIMIT 1')
        sequence = cursor.fetchone()

        if not sequence:
            conn.close()
            flash('No sequences available. Please contact the administrator.')
            return redirect(url_for('dashboard'))

        # Assign the sequence to the user
        cursor.execute('''
            INSERT INTO user_sequences (user_id, task1, task2, task3, task4)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, sequence[1], sequence[2], sequence[3], sequence[4]))

        # Increment the assigned count for the sequence
        cursor.execute('UPDATE sequences SET assigned_count = assigned_count + 1 WHERE sequence_id = ?', (sequence[0],))
        conn.commit()

        # Теперь получаем вновь вставленную запись, чтобы использовать её далее
        cursor.execute('SELECT task1, task2, task3, task4 FROM user_sequences WHERE user_id = ?', (user_id,))
        seq_row = cursor.fetchone()
    else:
        seq_row = (existing_sequence[1], existing_sequence[2], existing_sequence[3], existing_sequence[4])
    conn.close()

    # Приводим последовательность к нужному формату
    if seq_row:
        sequence = [task.lower().replace(' ', '_').replace('-', '_') for task in seq_row]
        session['sequence'] = sequence
    else:
        sequence = session.get('sequence')

    # Check if questionnaire completed
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM questionnaire_responses WHERE user_id = ? LIMIT 1', (user_id,))
    has_questionnaire = cursor.fetchone() is not None

    cursor.execute('SELECT task1, task2, task3, task4 FROM user_sequences WHERE user_id = ?', (user_id,))
    seq_row = cursor.fetchone()
    if seq_row:
        sequence = [task.lower().replace(' ', '_').replace('-', '_') for task in seq_row]
        session['sequence'] = sequence  # This line was missing
    else:
        sequence = session['sequence']

    # Load completed tasks from database
    cursor.execute('SELECT task_name FROM user_progress WHERE user_id = ?', (user_id,))
    db_completed = [row[0] for row in cursor.fetchall()]
    session_completed = session.get('completed_tasks', [])
    completed_tasks = list(set(db_completed + session_completed))
    session['completed_tasks'] = completed_tasks

    cursor.execute('''
        SELECT MAX(completed_at)
        FROM user_progress
        WHERE user_id = ?
    ''', (user_id,))
    last_active = cursor.fetchone()[0] or "Нет активности"

    conn.close()

    # Пример: загружаем информацию о завершённых заданиях
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT task_name FROM user_progress WHERE user_id = ?', (user_id,))
    completed_tasks = [row[0] for row in cursor.fetchall()]
    conn.close()

    # Если хотя бы одна игра завершена, вычисляем результаты
    results_dict = {}
    total = 0
    if completed_tasks:
        results_dict, total = get_user_results(user_id)

    # Determine next task
    next_task = None
    if has_questionnaire and sequence:
        # Get completed tasks from session or initialize
        completed_tasks = session.get('completed_tasks', [])
        # Debug: Print completed tasks and sequence
        print(f"Completed Tasks: {completed_tasks}")
        print(f"Sequence: {sequence}")

        # Find first incomplete task
        for task in sequence:
            if task not in completed_tasks:
                next_task = task
                break


    return render_template('dashboard.html',
                         has_questionnaire=has_questionnaire,
                         next_task=next_task,
                         completed_tasks=completed_tasks,
                         sequence=sequence,
                         last_active=last_active,
                         task_names=task_names,
                         results=results_dict,
                         total=total)

@app.route('/start_experiment', methods=['POST'])
def start_experiment():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # # Get the next sequence in round-robin order
    # conn = sqlite3.connect('database.db')
    # cursor = conn.cursor()
    # cursor.execute('SELECT * FROM sequences ORDER BY assigned_count ASC, sequence_id ASC LIMIT 1')
    # sequence = cursor.fetchone()

    # if not sequence:
    #     conn.close()
    #     flash('No sequences available. Please contact the administrator.')
    #     return redirect(url_for('dashboard'))

    # # Assign the sequence to the user
    # cursor.execute('''
    #     INSERT INTO user_sequences (user_id, task1, task2, task3, task4)
    #     VALUES (?, ?, ?, ?, ?)
    # ''', (user_id, sequence[1], sequence[2], sequence[3], sequence[4]))

    # # Increment the assigned count for the sequence
    # cursor.execute('UPDATE sequences SET assigned_count = assigned_count + 1 WHERE sequence_id = ?', (sequence[0],))
    # conn.commit()
    # conn.close()

    # # Store the sequence in the session
    # session['sequence'] = [
    #     task.lower().replace(' ', '_').replace('-', '_')
    #     for task in [sequence[1], sequence[2], sequence[3], sequence[4]]
    # ]
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
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Save questionnaire responses
        for i in range(1, 31):  # Loop through all 30 questions
            question_key = f'q{i}'
            response = request.form.get(question_key)
            if response:
                # Save the response to the database
                cursor.execute('''
                    INSERT INTO questionnaire_responses (user_id, question_number, response)
                    VALUES (?, ?, ?)
                ''', (user_id, i, int(response)))

        conn.commit()
        conn.close()

        # Redirect to the first task
        return redirect(url_for('task', task_name=session['sequence'][0]))

    return render_template('questionnaire.html', questions=QUESTIONS)

# Experimental design parameters
FACTORS = {
    'loss_cards': [1, 2, 3],
    'gain_amount': [10, 20, 30],
    'loss_amount': [250, 500, 750]
}

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
                        'trial_type': 'experimental'  # экспериментальный трейл
                    }
                    trials.append(trial)
        # 27 уникальных комбинаций; умножив на 2, получим 54 экспериментальных трейла
        experimental_trials = trials * 2

        # Генерируем 9 дополнительных случайных loss-трейлов
        random_loss_trials = []
        for _ in range(9):
            trial = random.choice(trials).copy()
            trial['trial_type'] = 'random_loss'  # маркируем как случайный loss трейл
            random_loss_trials.append(trial)

        # Объединяем экспериментальные и случайные трейлы (54 + 9 = 63)
        all_trials = experimental_trials + random_loss_trials
        random.shuffle(all_trials)
        return all_trials
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
        trials = trials * 2
        random.shuffle(trials)
        return trials


# def generate_balloon_sequence(max_pumps):
#     # Generate a sequence of numbers from 1 to max_pumps
#     sequence = list(range(1, max_pumps + 1))
#     random.shuffle(sequence)
#     return sequence

def mark_task_completed(user_id, task_name):
    device = get_device_type()
    conn = get_db()
    try:
        conn.execute('''
            INSERT OR IGNORE INTO user_progress (user_id, task_name, device_type)
            VALUES (?, ?, ?)
        ''', (user_id, task_name, device))
        conn.commit()
    finally:
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
            В каждой попытке вы можете выиграть какое-то количество денег, но в то же время есть риск попасться на штраф. После каждого выбора
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
            в виду, что в какой-то момент воздушный шар лопнет. Точка взрыва различается для разных воздушных шаров. Если шарик
            лопнет до того, как вы нажмете «Забрать», то вы перейдете к следующему шарику, и все деньги в вашем временном банке будут
            потеряны. Взорвавшиеся шарики не влияют на деньги, накопленные в вашем постоянном банке.'''
        },
        'cct_hot': {
            'title': 'Инструкция к заданию',
            'content': '''Перед вами расположено 32 карты: какие-то из них "хорошие" и могут принести вам деньги, а какие-то "плохие", и
            за их выбор предусмотрен штраф. Сверху у вас есть информация по текущему раскладу. Карты проигрыша - это количество "плохих" карт
            в раскладе. Награда за карту - это сумма, которую вы можете получить за выбор "хорошей" карты. Размер проигрыша - это штраф, который вы
            можете получить за выбор "плохой" карты. Вы можете выбрать столько карт, сколько посчитаете нужным. Как только вы закончите выбирать,
            нажмите на кнопку "Закончить попытку" или нажмите клавишу "Enter". Это позволит сохранить заработанные за текущую попытку деньги и перейти к новой попытке.
            Имейте в виду, что как только вы выберете "плохую" карту, ваша попытка будет окончена автоматически, и все заработанные деньги исчезнут.'''
        },
        'cct_cold': {
            'title': 'Инструкция к заданию',
            'content': '''Перед вами расположено 32 карты: какие-то из них "хорошие" и могут принести вам деньги, а какие-то "плохие", и за их
            выбор предусмотрен штраф. Награда за карту - это сумма, которую вы получите за каждую перевернутую «хорошую» карту.
            Размер проигрыша - это штраф, который вы получите, если среди перевернутых карт есть хотя бы одна плохая (независимо от того,
            сколько «хороших» карт Вы перевернули). Сверху у вас есть информация по текущему раскладу: размер выигрыша за каждую перевернутую
            «хорошую», размер проигрыша за весь раунд, если среди перевернутых карт окажется хотя бы одна «плохая», а также количество плохих
            карт в раскладе (все остальные карты считаются хорошими). Вы можете перевернуть столько карт, сколько посчитаете нужным.
            Как только вы определитесь с выбором, вам необходимо нажать на кнопку с числом, соответствующим количеству карт, которое вы решили
            перевернуть.
            В игре будет несколько раундов. Вы не получите никакой обратной связи по поводу количества заработанных или потерянных денег до конца игры.
            '''
        }
    }

    if task_name not in session.get('completed_tasks', []):
        # Можно использовать проверку request.referrer для определения, что пользователь пришёл не с той же страницы игры.
        # Например, для BART:
        if task_name == 'bart':
            bart_url = url_for('task', task_name='bart')
            if not (request.referrer and request.referrer.endswith(bart_url)):
                user_id = session.get('user_id')
                if user_id:
                    conn = get_db()
                    # Удаляем все записи для IGT данного пользователя
                    conn.execute('DELETE FROM bart_results WHERE user_id = ?', (user_id,))
                    conn.commit()
                    conn.close()
                # Сброс переменных игры BART
                session.pop('bart_current', None)
                session.pop('bart_total_points', None)
                session.pop('bart_trials', None)
                session.pop('bart_balloon_types', None)
                session.pop('bart_balloon_sequences', None)
                session.pop(f'{task_name}_instructions_viewed', None)
                # Инициализация заново
                session['bart_trials'] = 90  # число раундов
                session['bart_current'] = 0
                session['bart_total_points'] = 0
                session['bart_balloon_types'] = ['blue', 'yellow', 'orange'] * 30
                random.shuffle(session['bart_balloon_types'])
                # session['bart_balloon_sequences'] = {
                #     'blue': generate_balloon_sequence(128),
                #     'yellow': generate_balloon_sequence(32),
                #     'orange': generate_balloon_sequence(8)
                # }
        elif task_name == 'igt':
            igt_url = url_for('task', task_name='igt')
            if not (request.referrer and request.referrer.endswith(igt_url)):
                user_id = session.get('user_id')
                if user_id:
                    conn = get_db()
                    # Удаляем все записи для IGT данного пользователя
                    conn.execute('DELETE FROM igt_results WHERE user_id = ?', (user_id,))
                    conn.commit()
                    conn.close()
                # Сброс session-переменных (если требуется)
                session.pop(f'{task_name}_instructions_viewed', None)
                session['igt_trials'] = 100
                session['igt_current'] = 0
                session['igt_total_points'] = 2000
        elif task_name in ['cct_hot', 'cct_cold']:
            cct_url = url_for('task', task_name=task_name)
            if not (request.referrer and request.referrer.endswith(cct_url)):
                user_id = session.get('user_id')
                if user_id:
                    conn = get_db()
                    # Удаляем все записи для IGT данного пользователя
                    conn.execute(f'DELETE FROM {task_name}_results WHERE user_id = ?', (user_id,))
                    conn.commit()
                    conn.close()
                session.pop(f'{task_name}_current', None)
                session.pop(f'{task_name}_trials', None)
                session.pop(f'{task_name}_instructions_viewed', None)
                session[f'{task_name}_trials'] = generate_trials(task=task_name)
                session[f'{task_name}_current'] = 0

    if task_name not in session.get('sequence', []):
        return redirect(url_for('dashboard'))

    # NEW: Database completion check (insert here)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 1 FROM user_progress
        WHERE user_id = ? AND task_name = ?
    ''', (session['user_id'], task_name))
    if cursor.fetchone():
        conn.close()
        return redirect(url_for('dashboard'))
    conn.close()



    # Handle IGT task
    if task_name == 'igt':
        # Get actual progress from database
        conn = get_db()
        cursor = conn.cursor()

        # Get current trial number
        cursor.execute('SELECT COUNT(*) FROM igt_results WHERE user_id = ?', (session['user_id'],))
        current_trial = cursor.fetchone()[0]

        # Get total points
        cursor.execute('SELECT SUM(points_earned) FROM igt_results WHERE user_id = ?', (session['user_id'],))
        total_points = 2000 + (cursor.fetchone()[0] or 0)

        conn.close()

        # Check if instructions need to be shown
        instruction_key = f'{task_name}_instructions_viewed'
        show_instructions = not session.get(instruction_key, False)

        return render_template(
            'igt.html',
            current_trial=current_trial + 1,  # Display next trial number
            total_trials=100,
            total_points=total_points,
            instruction_title=instructions[task_name]['title'],
            instruction_content=instructions[task_name]['content'],
            show_instructions=show_instructions
        )

    # Handle BART task
    if task_name == 'bart':
        # Initialize session variables if they don't exist
        if 'bart_trials' not in session:
            session['bart_trials'] = 90  # 30 trials per balloon type × 3 types
        if 'bart_current' not in session:
            session['bart_current'] = 0
        if 'bart_total_points' not in session:
            session['bart_total_points'] = 0
        if 'bart_balloon_types' not in session:
            session['bart_balloon_types'] = ['blue', 'yellow', 'orange'] * 30
            random.shuffle(session['bart_balloon_types'])
        # if 'bart_balloon_sequences' not in session:
        #     session['bart_balloon_sequences'] = {
        #         'blue': generate_balloon_sequence(128),
        #         'yellow': generate_balloon_sequence(32),
        #         'orange': generate_balloon_sequence(8)
        #     }

        # After committing the insert
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT points_earned
            FROM bart_results
            WHERE user_id = ?
            ORDER BY rowid DESC
            LIMIT 1
        ''', (session['user_id'],))

        last_points = cursor.fetchone()
        if last_points:
            last_points_earned = last_points[0]
        else:
            last_points_earned = 0  # Default value if no records found

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

        # Ensure session variables are initialized
        if 'bart_balloon_types' not in session:
            session['bart_balloon_types'] = ['blue', 'yellow', 'orange'] * 30  # 30 trials per color
            random.shuffle(session['bart_balloon_types'])  # Randomize balloon order
            # session['bart_balloon_sequences'] = {
            #     'blue': generate_balloon_sequence(128),  # Average break point: 64
            #     'yellow': generate_balloon_sequence(32),  # Average break point: 16
            #     'orange': generate_balloon_sequence(8)    # Average break point: 4
            # }

        # Get the current balloon type and sequence
        balloon_type = session['bart_balloon_types'][session['bart_current']]
        #balloon_sequence = session['bart_balloon_sequences'][balloon_type]

        if balloon_type == 'blue':
            max_pumps = 128
        elif balloon_type == 'yellow':
            max_pumps = 32
        elif balloon_type == 'orange':
            max_pumps = 8
        else:
            max_pumps = 128  # Значение по умолчанию

        # Генерируем точку взрыва для текущего раунда (trial)
        explosion_point = random.randint(1, max_pumps)

        # Check if instructions need to be shown
        instruction_key = f'{task_name}_instructions_viewed'
        show_instructions = not session.get(instruction_key, False)

        # Render the BART template
        return render_template(
            valid_tasks[task_name],
            trial_number=session['bart_current'] + 1,
            total_trials=session['bart_trials'],
            total_points=session['bart_total_points'],
            balloon_type=balloon_type,
            #balloon_sequence=balloon_sequence,
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
        trial_type = current_trial.get('trial_type', 'experimental')
        total_trials = len(session[f'{task_name}_trials'])  # will be 63

        instruction_key = f'{task_name}_instructions_viewed'
        show_instructions = not session.get(instruction_key, False)

        return render_template(
            valid_tasks[task_name],
            loss_cards=loss_cards,
            gain_amount=gain_amount,
            loss_amount=loss_amount,
            trial_number=f"{trial_number}/{total_trials}",
            instruction_title=instructions[task_name]['title'],
            instruction_content=instructions[task_name]['content'],
            show_instructions=show_instructions,
            trial_type=trial_type  # new parameter
        )

    # Render appropriate template for other tasks
    return render_template(valid_tasks[task_name])

@app.route('/save_cct_hot', methods=['POST'])
def save_cct_hot():
    data = request.get_json()
    user_id = session.get('user_id')
    task_name = 'cct_hot'

     # Initialize if missing
    if f'{task_name}_current' not in session:
        session[f'{task_name}_current'] = 0
    if f'{task_name}_trials' not in session:
        session[f'{task_name}_trials'] = generate_trials(task=task_name)

    # Save results to database
    #conn = get_db()

    # conn.execute('''
    #     INSERT INTO cct_hot_results (user_id, points, trial_number)
    #     VALUES (?, ?, ?)
    # ''', (user_id, data['points'], data['trialNumber']))
    # conn.commit()
    # conn.close()

    # Get the current trial data
    current_trial = session['cct_hot_trials'][session['cct_hot_current']]
    loss_cards = current_trial['loss_cards']
    gain_amount = current_trial['gain_amount']
    loss_amount = current_trial['loss_amount']
    num_cards = data['flipped_cards']
    reaction_times_json = json.dumps(data.get('reaction_time', []))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cct_hot_results (user_id, points, trial_number, reaction_time, flipped_cards, loss_cards, gain_amount, loss_amount, trial_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, data['points'], data['trialNumber'], reaction_times_json, num_cards, loss_cards, gain_amount, loss_amount, current_trial.get('trial_type', 'experimental')))
    conn.commit()
    conn.close()

    # Update trial counter
    session['cct_hot_current'] += 1

    # Check if final trial
    is_final_trial = session['cct_hot_current'] >= len(session['cct_hot_trials'])

        # После сохранения данных
    if is_final_trial:
        mark_task_completed(user_id, 'cct_hot')
        if 'completed_tasks' not in session:
            session['completed_tasks'] = []
        if 'cct_hot' not in session['completed_tasks']:
            session['completed_tasks'].append('cct_hot')

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

    # Рассчитываем очки
    if loss_encountered:
        points_earned = -loss_amount
    else:
        points_earned = num_cards * gain_amount

    # Save results to database
    conn = get_db()
    conn.execute('''
        INSERT INTO cct_cold_results (user_id, trial_number, num_cards, loss_encountered, points_earned, reaction_time, loss_cards, gain_amount, loss_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, data['trialNumber'], num_cards, loss_encountered, points_earned, data['reaction_time'], loss_cards, gain_amount, loss_amount))
    conn.commit()
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
        'redirect_url': url_for('intermediate', task_name='cct_cold') if is_final_trial else None
    })

@app.route('/save_igt', methods=['POST'])
def save_igt():
    data = request.get_json()
    user_id = session.get('user_id')
    task_name = 'igt'

    #Initialize session variables
    session.setdefault('igt_trials', 100)
    session.setdefault('igt_current', 0)
    session.setdefault('igt_total_points', 2000)

    # Define deck payouts and penalties
    deck_payouts = {
        'A': 100,
        'B': 100,
        'C': 50,
        'D': 50
    }
    deck_penalties = {
        'A': 250,
        'B': 250,
        'C': 50,
        'D': 50
    }

     # Initialize if missing
    if f'{task_name}_current' not in session:
        session[f'{task_name}_current'] = 0
    if f'{task_name}_trials' not in session:
        session[f'{task_name}_trials'] = generate_trials()

    # Get selected deck from client
    selected_deck = data['deck']

    payout = deck_payouts[selected_deck]
    penalty = deck_penalties[selected_deck] if random.random() < 0.5 else 0
    points_earned = payout - penalty

    # Update session variables
    session['igt_total_points'] += points_earned
    session['igt_current'] += 1
    session.modified = True

    # Save results to database
    conn = get_db()
    conn.execute('''
        INSERT INTO igt_results (user_id, trial_number, deck, payout, penalty, points_earned, reaction_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, session['igt_current'], selected_deck, payout, penalty, points_earned, data['reaction_time']))
    conn.commit()
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
        # Check if task is already completed
        # conn = get_db()
        # cursor = conn.cursor()
        # cursor.execute('SELECT 1 FROM user_progress WHERE user_id = ? AND task_name = ?',
        #               (session['user_id'], 'igt'))
        # if cursor.fetchone():
        #     conn.close()
        #     return redirect(url_for('dashboard'))
        # conn.close()

        # Update trial counter

        session.modified = True

        if session['igt_current'] >= session.get('igt_trials', 100):
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
    user_id = session.get('user_id')
    task_name = 'bart'

     # Initialize if missing
    if f'{task_name}_current' not in session:
        session[f'{task_name}_current'] = 0
    if f'{task_name}_trials' not in session:
        session[f'{task_name}_trials'] = generate_trials()

     # Get data from request
    popped = data.get('popped', False)
    points_earned = 0 if popped else data.get('pointsEarned', 0)
    pumps = data.get('pumps', 0)
    balloon_type = data.get('balloonType', 'unknown')

    # Calculate actual points earned
    if not popped:
        session['bart_total_points'] = session.get('bart_total_points', 0) + points_earned

    # Save results to database
    conn = get_db()
    conn.execute('''
        INSERT INTO bart_results (user_id, trial_number, balloon_type, pumps, popped, points_earned, reaction_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, data['trialNumber'], balloon_type, pumps, popped, points_earned, data['reaction_time']))
    conn.commit()
    conn.close()

    # Update session variables

    session['bart_current'] += 1

    # Check if final trial
    is_final_trial = session['bart_current'] >= session['bart_trials']

    # После сохранения данных
    if is_final_trial:
        mark_task_completed(user_id, 'bart')
        if 'completed_tasks' not in session:
            session['completed_tasks'] = []
        if 'bart' not in session['completed_tasks']:
            session['completed_tasks'].append('bart')

    return jsonify({
        'new_total_points': session['bart_total_points'],
        'status': 'completed' if is_final_trial else 'success',
        'redirect_url': url_for('intermediate', task_name='bart') if is_final_trial else None,
        'points_earned':points_earned
    })

@app.route('/intermediate/<task_name>')
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
            cursor.execute(f'SELECT SUM(points) FROM {task_name}_results WHERE user_id = ?',
                          (session['user_id'],))
        elif task_name == "cct_cold":
            cursor.execute(f'SELECT SUM(points_earned) FROM {task_name}_results WHERE user_id = ?',
                          (session['user_id'],))
        total_money = cursor.fetchone()[0] or 0
        conn.close()

    return render_template('intermediate.html',
                         task_name=task_name,
                         next_task=next_task,
                         total_money=total_money)

def get_user_results(user_id):
    conn = get_db()
    cursor = conn.cursor()
    results = {}
    total_earnings = 0

    # Пример для IGT
    cursor.execute('SELECT SUM(points_earned) FROM igt_results WHERE user_id = ?', (user_id,))
    igt_total = cursor.fetchone()[0] or 0
    results['Выбор одной карты из четырёх'] = igt_total
    total_earnings += igt_total

    # Пример для BART
    cursor.execute('SELECT SUM(points_earned) FROM bart_results WHERE user_id = ?', (user_id,))
    bart_total = cursor.fetchone()[0] or 0
    results['Надуть шарик'] = bart_total
    total_earnings += bart_total

    # Пример для CCT-hot
    cursor.execute('SELECT SUM(points) FROM cct_hot_results WHERE user_id = ?', (user_id,))
    cct_hot_total = cursor.fetchone()[0] or 0
    results['Выбрать N карт последовательно'] = cct_hot_total
    total_earnings += cct_hot_total

    # Пример для CCT-cold
    cursor.execute('SELECT SUM(points_earned) FROM cct_cold_results WHERE user_id = ?', (user_id,))
    cct_cold_total = cursor.fetchone()[0] or 0
    results['Выбрать N карт одновременно'] = cct_cold_total
    total_earnings += cct_cold_total

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
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM user_progress WHERE user_id = ?', (user_id,))
    completed = cur.fetchone()[0]
    conn.close()
    if completed == 0:
        flash("Результаты появятся после завершения хотя бы одной игры.", "info")
        return redirect(url_for('dashboard'))

    # Считаем все метрики
    questionnaire = get_questionnaire_results(user_id)
    bart          = get_bart_metrics(user_id)
    igt           = get_igt_metrics(user_id)
    cct_hot       = get_cct_hot_metrics(user_id)
    cct_cold      = get_cct_cold_metrics(user_id)

    return render_template(
        'results.html',
        questionnaire=questionnaire,
        bart=bart,
        igt=igt,
        cct_hot=cct_hot,
        cct_cold=cct_cold
    )

@app.route('/test')
def test():
    return render_template("test.html")

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

def get_questionnaire_results(user_id):
    conn = get_db()
    cur = conn.cursor()

    # Получаем все ответы
    cur.execute('SELECT question_number, response FROM questionnaire_responses WHERE user_id = ?', (user_id,))
    responses = cur.fetchall()

    # Вопросы, требующие обратного кодирования
    reverse_scored = {4, 5, 13, 14, 15, 16, 17, 19, 20, 21, 26}
    total_score = 0

    for row in responses:
        qnum, response = row['question_number'], row['response']
        if qnum in reverse_scored:
            response = 5 - response  # обратное кодирование
        total_score += response

    # Процентиль среди всех участников
    cur.execute('SELECT user_id FROM questionnaire_responses GROUP BY user_id')
    all_user_ids = [row['user_id'] for row in cur.fetchall()]

    scores = []
    for uid in all_user_ids:
        cur.execute('SELECT question_number, response FROM questionnaire_responses WHERE user_id = ?', (uid,))
        user_responses = cur.fetchall()
        user_score = 0
        for row in user_responses:
            qnum, response = row['question_number'], row['response']
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

    conn.close()
    return {
        'total_score': total_score,
        'percentile': percentile
    }


#
# 2) Метрики BART
#
def get_bart_metrics(user_id):
    conn = get_db()
    cur = conn.cursor()
    # Пользовательские
    cur.execute('''
        SELECT
            AVG(pumps) AS avg_pumps,
            AVG(CASE WHEN popped = 1 THEN 1.0 ELSE 0 END) AS explosion_rate,
            SUM(points_earned) AS total_earn
        FROM bart_results
        WHERE user_id = ?
    ''', (user_id,))
    row = cur.fetchone()
    avg_pumps = row['avg_pumps'] or 0.0
    explosion_rate = row['explosion_rate'] or 0.0
    total_earn = row['total_earn'] or 0

    # Групповые средние
    cur.execute('SELECT AVG(pumps) FROM bart_results')
    grp_avg_pumps = cur.fetchone()[0] or 0.0
    cur.execute('SELECT AVG(CASE WHEN popped = 1 THEN 1.0 ELSE 0 END) FROM bart_results')
    grp_explosion = cur.fetchone()[0] or 0.0
    cur.execute('SELECT AVG(points_earned) FROM bart_results')
    grp_avg_earn = cur.fetchone()[0] or 0.0

    conn.close()

    # Относительные отклонения от среднего (в %)
    pct_pumps = round(100 * (avg_pumps / grp_avg_pumps - 1), 1) if grp_avg_pumps else 0.0
    pct_earn = round(100 * (total_earn / grp_avg_earn - 1), 1)    if grp_avg_earn  else 0.0
    pct_explosion = round(100 * (explosion_rate / grp_explosion - 1), 1) if grp_explosion else 0.0

    return {
        'avg_pumps': round(avg_pumps, 1),
        'explosion_rate': round(100 * explosion_rate, 1),
        'total_earn': total_earn,
        'pct_pumps': pct_pumps,
        'pct_earn': pct_earn,
        'pct_explosion': pct_explosion
    }

#
# 3) Метрики IGT
#
def get_igt_metrics(user_id):
    conn = get_db()
    cur = conn.cursor()

    # Сумма и среднее
    cur.execute('''
        SELECT
            SUM(points_earned)  AS total_net,
            AVG(points_earned)  AS avg_net
        FROM igt_results
        WHERE user_id = ?
    ''', (user_id,))
    row = cur.fetchone()
    total_net = row['total_net'] or 0
    avg_net   = row['avg_net']   or 0.0

    # Доля выгодных выборов (колоды C или D)
    cur.execute('''
        SELECT COUNT(*) * 1.0 / (
            SELECT COUNT(*) FROM igt_results WHERE user_id = ?
        ) AS pct_good
        FROM igt_results
        WHERE user_id = ? AND deck IN ('C','D')
    ''', (user_id, user_id))
    pct_good = round(100 * (cur.fetchone()[0] or 0.0), 1)

    # Процентиль по total_net
    cur.execute('''
        SELECT SUM(points_earned) AS sum_net
        FROM igt_results
        GROUP BY user_id
    ''')
    all_nets = sorted([r['sum_net'] for r in cur.fetchall()])
    if all_nets:
        rank = all_nets.index(total_net) + 1
        pct_net = round(100 * rank / len(all_nets), 1)
    else:
        pct_net = 0.0

    conn.close()
    return {
        'total_net': total_net,
        'avg_net': round(avg_net, 1),
        'pct_good': pct_good,
        'pct_net': pct_net
    }

#
# 4) Метрики для CCT-hot и CCT-cold
#
def get_cct_hot_metrics(user_id):
    """Метрики для CCT-hot: flipped_cards и points"""
    conn = get_db()
    cur = conn.cursor()

    # Пользовательские метрики (только experimental trials)
    cur.execute('''
        SELECT
            AVG(flipped_cards)    AS avg_flip,
            AVG(points)           AS avg_pts
        FROM cct_hot_results
        WHERE user_id = ? AND trial_type = 'experimental'
    ''', (user_id,))
    row = cur.fetchone()
    avg_flip = row['avg_flip'] or 0.0
    avg_pts  = row['avg_pts']  or 0.0

    # Групповые средние
    cur.execute('''
        SELECT
            AVG(flipped_cards),
            AVG(points)
        FROM cct_hot_results
        WHERE trial_type = 'experimental'
    ''')
    grp = cur.fetchone()
    grp_flip = grp[0] or 1.0
    grp_pts  = grp[1] or 1.0

    conn.close()

    return {
        'avg_flip': round(avg_flip,1),
        'avg_pts':  round(avg_pts,1),
        'pct_flip': round(100*(avg_flip/grp_flip - 1),1),
        'pct_pts':  round(100*(avg_pts/grp_pts   - 1),1)
    }


def get_cct_cold_metrics(user_id):
    """Метрики для CCT-cold: num_cards и points_earned"""
    conn = get_db()
    cur = conn.cursor()

    # Пользовательские метрики (всех trials)
    cur.execute('''
        SELECT
            AVG(num_cards)        AS avg_num,
            AVG(points_earned)    AS avg_pts
        FROM cct_cold_results
        WHERE user_id = ?
    ''', (user_id,))
    row = cur.fetchone()
    avg_num = row['avg_num'] or 0.0
    avg_pts = row['avg_pts'] or 0.0

    # Групповые средние
    cur.execute('''
        SELECT
            AVG(num_cards),
            AVG(points_earned)
        FROM cct_cold_results
    ''')
    grp = cur.fetchone()
    grp_num = grp[0] or 1.0
    grp_pts = grp[1] or 1.0

    conn.close()

    return {
        'avg_num': round(avg_num,1),
        'avg_pts': round(avg_pts,1),
        'pct_num': round(100*(avg_num/grp_num - 1),1),
        'pct_pts': round(100*(avg_pts/grp_pts - 1),1)
    }

if __name__ == '__main__':
    app.run(debug=True)

