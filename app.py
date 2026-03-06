from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_key"

# Database helper
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- Home ----------------
@app.route('/')
def home():
    return render_template('index.html')

# ---------------- Register ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        age = request.form['age']
        fitness_goal = request.form['fitness_goal']
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            'INSERT INTO members (name, phone, age, fitness_goal, username, password) VALUES (?,?,?,?,?,?)',
            (name, phone, age, fitness_goal, username, password)
        )
        conn.commit()
        conn.close()
        flash("Registration successful! Please login.", "success")
        return redirect('/login')
    return render_template('register.html')

# ---------------- Login ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM members WHERE username=?", (username,))
        member = c.fetchone()
        conn.close()

        if member and check_password_hash(member['password'], password):
            session['member_id'] = member['id']
            return redirect('/dashboard')
        else:
            flash("Invalid username or password!", "danger")
            return redirect('/login')
    return render_template('login.html')

# ---------------- Dashboard ----------------
@app.route('/dashboard')
def dashboard():
    if 'member_id' not in session:
        return redirect('/login')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM members WHERE id=?", (session['member_id'],))
    member = c.fetchone()
    conn.close()
    return render_template('dashboard.html', member=member)

# ---------------- Logout ----------------
@app.route('/logout')
def logout():
    session.pop('member_id', None)
    return redirect('/')

# ---------------- Personal Profile ----------------
@app.route('/profile', methods=['GET','POST'])
def profile():
    if 'member_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        age = request.form['age']
        fitness_goal = request.form['fitness_goal']
        c.execute("UPDATE members SET name=?, phone=?, age=?, fitness_goal=? WHERE id=?",
                  (name, phone, age, fitness_goal, session['member_id']))
        conn.commit()

    c.execute("SELECT * FROM members WHERE id=?", (session['member_id'],))
    member = c.fetchone()
    conn.close()
    return render_template('profile.html', member=member)

if __name__ == "__main__":
    app.run(debug=True, port=8080)