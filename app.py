from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.urandom(16)

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                status TEXT DEFAULT NULL
            )
        ''')
init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

### Webapp routing ###

@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')

    username = session['user']
    
    with get_db_connection() as conn:
        row = conn.execute("SELECT status FROM users WHERE username = ?", (username,)).fetchone()
        status = row['status'] if row else None
        
        user_status_rows = conn.execute("SELECT username, status FROM users").fetchall()
        user_status = {row['username']: row['status'] for row in user_status_rows}

    return render_template(
        'home.html',
        username=username,
        status=status,
        user_status=user_status
    )

def get_pending_users():
    with get_db_connection() as conn:
        rows = conn.execute("SELECT username FROM users WHERE status IS NULL").fetchall()
    return [row['username'] for row in rows]


@app.route('/set_status', methods=['POST'])
def set_status():
    if 'user' not in session:
        return redirect('/login')

    username = session['user']
    new_status = request.form['status']

    with get_db_connection() as conn:
        conn.execute("UPDATE users SET status = ? WHERE username = ?", (new_status, username))
        conn.commit()

    return redirect('/')

@app.route('/admin')
def admin():
    if 'user' not in session or session['user'] != 'Ruka Kawai':
        return redirect('/login')

    with get_db_connection() as conn:
        users = conn.execute("SELECT username, status FROM users").fetchall()
    pending_users = get_pending_users()

    return render_template(
        'admin.html',
        users=users,
        pending_users=pending_users
    )

@app.route('/admin/start_next_round', methods=['POST'])
def start_next_round():
    if 'user' not in session or session['user'] != 'Ruka Kawai':
        return redirect('/login')

    with get_db_connection() as conn:
        conn.execute("UPDATE users SET status = NULL")
        conn.commit()

    return redirect('/admin')


@app.route('/admin/set_status', methods=['POST'])
def admin_set_status():
    if 'user' not in session or session['user'] != 'Ruka Kawai':
        return redirect('/login')
    
    new_status = request.form['status']
    username = session['user']

    with get_db_connection() as conn:
        conn.execute("UPDATE users SET status = ? WHERE username = ?", (new_status, username))
        conn.commit()

    return redirect('/admin')

@app.route('/reset_all', methods=['POST'])
def reset_all():
    if 'user' not in session or session['user'] != 'Ruka Kawai':
        return redirect('/login')
    
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET status = NULL")
        conn.commit()
    
    return redirect('/admin')

@app.route('/reset/<username>', methods=['POST'])
def reset_user(username):
    conn = get_db_connection()
    conn.execute("UPDATE users SET status = NULL WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if 'user' not in session or session['user'] != 'Ruka Kawai':
        return redirect('/login')

    message = ''
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])

        try:
            with get_db_connection() as conn:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            message = "User registered successfully!"
        except sqlite3.IntegrityError:
            message = "Username already exists."

    return render_template('admin_register.html', message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']

        if username == "Ruka Kawai" and password_input == "Shin Haram":
            session['user'] = username
            return redirect('/admin')

        password = hash_password(password_input)
        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        if user:
            session['user'] = username
            return redirect('/')
        else:
            msg = "Invalid credentials."

    return render_template('login.html', message=msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])

        try:
            with get_db_connection() as conn:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            message = "User registered successfully!"
        except sqlite3.IntegrityError:
            message = "Username already exists."
        return redirect('/login')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
