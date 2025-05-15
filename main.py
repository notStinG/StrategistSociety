from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib
import os
import random

app = Flask(__name__)
app.secret_key = os.urandom(16)
print("Test")
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
                status TEXT DEFAULT NULL,
                points INTEGER DEFAULT 0
            )
        ''')
init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

### SWISS LOGIC ###
cache = set()
CURRENT_STANDINGS = {}
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

def setup():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, points FROM users")
        result = cursor.fetchall()
        for name, points in result:
            CURRENT_STANDINGS[name] = points

def fetch_results():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, status FROM users")
        result = cursor.fetchall()

        if len(result) % 2 == 1:
            return "Odd pairings. Please insert another player"
        
        cursor.execute("UPDATE users SET status = NULL")
        conn.commit()

def order():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, points FROM users ORDER BY points DESC")
        return cursor.fetchall()


def calculate_swiss():
    pairings = []
    sorted_pos = order()

    # Sort based off pts
    grps = []
    grp = []
    for i in range(len(sorted_pos)-1):
        if sorted_pos[i][1] == sorted_pos[i+1][1]:
            grp.append(sorted_pos[i][0])
        else:
            grp.append(sorted_pos[i][0])
            grps.append(grp)
            grp = []
    grp.append(sorted_pos[-1][0])
    grps.append(grp)

    temp = []
    for grp in grps:
        if temp:
            for name in temp:
                grp.append(name)
            temp = []
        if (len(grp)%2) == 1:
            temp = [grp.pop()]
        
        # Now pair the players in this group
        while len(grp) >= 2:
            # Get all possible valid pairs that haven't been matched before
            valid_pairs = []
            for i in range(len(grp)):
                for j in range(i+1, len(grp)):
                    pair = tuple(sorted((grp[i], grp[j])))  
                    if pair not in cache:
                        valid_pairs.append((i, j, pair))
            
            if not valid_pairs:
                # No valid pairs left, have to rematch
                i, j = 0, 1
                pair = tuple(sorted((grp[i], grp[j])))
            else:
                # Randomly select one of the valid pairs
                i, j, pair = random.choice(valid_pairs)
            
            # Add the pair to pairings and cache
            pairings.append((grp[i], grp[j]))
            cache.add(pair)
            
            # Remove the paired players from the group
            # Remove the higher index first to avoid index errors
            grp.pop(max(i, j))
            grp.pop(min(i, j))
    return pairings
        
### Webapp routing stuff ###
# home page
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')

    username = session['user']
    
    if username == 'Ruka Kawai':
        return redirect('/admin')

    with get_db_connection() as conn:
        row = conn.execute("SELECT status FROM users WHERE username = ?", (username,)).fetchone()
        status = row['status'] if row else None
        
        user_status_rows = conn.execute("SELECT username, status FROM users").fetchall()
        user_status = {row['username']: row['status'] for row in user_status_rows}

    return render_template(
        'home.html',
        username=username,
        status=status,
        pairings=cache,
        standings=CURRENT_STANDINGS,
        user_status=user_status
    )

@app.route('/set_status', methods=['POST'])
def set_status():
    if 'user' not in session:
        return redirect('/login')

    username = session['user']
    new_status = request.form['status']

    with get_db_connection() as conn:
        row = conn.execute("SELECT status FROM users WHERE username = ?", (username,)).fetchone()
        old_status = row['status'] if row else None
        conn.execute("UPDATE users SET status = ? WHERE username = ?", (new_status, username))
        conn.commit()

    return redirect('/')



@app.route('/admin')
def admin():
    if 'user' not in session or session['user'] != 'Ruka Kawai':
        return redirect('/login')

    with get_db_connection() as conn:
        users = conn.execute("SELECT username, status, points FROM users").fetchall()
        # Get admin's current status
        admin_status = conn.execute("SELECT status FROM users WHERE username = ?", ('Ruka Kawai',)).fetchone()
        pending_users = conn.execute("SELECT username FROM users WHERE status IS NULL").fetchall()
    
    CURRENT_STANDINGS.clear()
    setup()
    fetch_results()
    pairings = calculate_swiss()
    standings = order()
    
    return render_template(
        'admin.html',
        users=users,
        pairings=pairings,
        standings=standings,
        status=admin_status['status'] if admin_status else None,
        pending_users=[row['username'] for row in pending_users]
    )
    
@app.route('/admin/set_status', methods=['POST'])
def admin_set_status():
    if 'user' not in session or session['user'] != 'Ruka Kawai':
        return redirect('/login')
    
    # with get_db_connection() as conn:
    #     conn.execute("UPDATE users SET status = 'TEST' WHERE username = 'Ruka Kawai'")
    #     conn.commit()

    #     row = conn.execute("SELECT status FROM users WHERE username = 'Ruka Kawai'").fetchone()
    # print("New status after update:", row['status'])

    new_status = request.form['status']
    username = session['user']

    with get_db_connection() as conn:
        row = conn.execute("SELECT status FROM users WHERE username = ?", (username,)).fetchone()
        old_status = row['status'] if row else None
        print(new_status)
        print(old_status)

        conn.execute("UPDATE users SET status = ? WHERE username = ?", (new_status, username))
        conn.commit()

        # after_status = conn.execute("SELECT status FROM users WHERE username = 'Ruka Kawai'").fetchone()
        # print("After update:", after_status['status'])


    return redirect('/admin')


@app.route('/reset_all', methods=['POST'])
def reset_all():
    if 'user' not in session or session['user'] != 'Ruka Kawai':
        return redirect('/login')
    
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET status = NULL")
        conn.commit()
    
    return redirect('/admin')

@app.route('/reset_points', methods=['POST'])
def reset_points():
    if 'user' not in session or session['user'] != 'Ruka Kawai':
        return redirect('/login')
    
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET points = 0, status = NULL")
        conn.commit()
    
    return redirect('/admin')

@app.route('/reset/<username>', methods=['POST'])
def reset_user(username):
    conn = get_db_connection()
    conn.execute("UPDATE users SET status = NULL WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return redirect('/admin')

# hardcoded ahhh username
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

# Next round
@app.route('/admin/next_round', methods=['POST'])
def next_round():
    if 'user' not in session or session['user'] != 'Ruka Kawai':
        return redirect('/login')

    with get_db_connection() as conn:
        users = conn.execute("SELECT username, status FROM users").fetchall()

        for user in users:
            username = user['username']
            status = user['status']

            if status == "Win":
                conn.execute("UPDATE users SET points = points + 1 WHERE username = ?", (username,))
            elif status == "Lost":
                conn.execute("UPDATE users SET points = points - 1 WHERE username = ?", (username,))
            else: 
                continue

        conn.execute("UPDATE users SET status = NULL")
        conn.commit()

    global cache
    cache.clear()

    CURRENT_STANDINGS.clear()
    setup()
    fetch_results()
    pairings = calculate_swiss()
    standings = order()

    return redirect('/admin')



# more unsafe hardcoded stuff u better pray this souce code aint leaking out
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
        conn.close()
        return redirect('/login')
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
