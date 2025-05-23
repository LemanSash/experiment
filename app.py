from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3, random

app = Flask(__name__)
app.secret_key = '#'

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS users (
                   user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT UNIQUE NOT NULL,
                   password_hash TEXT NOT NULL,
                   age INTEGER,
                   gender TEXT,
                   education TEXT
                   )
                   ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
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
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another.')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        if user and user[0] == password: #here should be password verification
            flash('Login successfull!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username of password.')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    if request.method == 'POST':
        # Save questionnaire responses
        q1 = request.form['q1']
        q2 = request.form['q2']
        q3 = request.form['q3']
        total_score = int(q1) + int(q2) + int(q3)
        
        # Assign a random task sequence
        methods = ["Iowa Gambling Task", "Balloon Analogue Risk Task", "Columbia Card Task-hot", "Columbia Card Task-cold"]
        random_sequence = random.sample(methods, len(methods))
        
        # Save sequence to database
        user_id = session['user_id']  # Assume user_id is stored in session after login
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO task_sequence (user_id, task1, task2, task3, task4)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, random_sequence[0], random_sequence[1], random_sequence[2], random_sequence[3]))
        conn.commit()
        conn.close()
        
        # Redirect to the first task
        return redirect(url_for('task', task_name=random_sequence[0]))
    return render_template('questionnaire.html')

@app.route('/task/<task_name>', methods=['GET', 'POST'])
def task(task_name):
    user_id = session['user_id']
    if request.method == 'POST':
        # Save task results (if applicable)
        pass
    
    # Mark task as completed
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if task_name == "Iowa Gambling Task":
        cursor.execute('UPDATE task_progress SET task1_completed = TRUE WHERE user_id = ?', (user_id,))
    elif task_name == "Balloon Analogue Risk Task":
        cursor.execute('UPDATE task_progress SET task2_completed = TRUE WHERE user_id = ?', (user_id,))
    elif task_name == "Columbia Card Task-hot":
        cursor.execute('UPDATE task_progress SET task3_completed = TRUE WHERE user_id = ?', (user_id,))
    elif task_name == "Columbia Card Task-cold":
        cursor.execute('UPDATE task_progress SET task4_completed = TRUE WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    # Render the task template
    if task_name == "Iowa Gambling Task":
        return render_template('igt.html')
    elif task_name == "Balloon Analogue Risk Task":
        return render_template('bart.html')
    elif task_name == "Columbia Card Task-hot":
        return render_template('cct_hot.html')
    elif task_name == "Columbia Card Task-cold":
        return render_template('cct_cold.html')
    else:
        return "Task not found", 404

    
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
            
