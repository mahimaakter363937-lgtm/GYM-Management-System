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

# ---------------- Fitness Profile ----------------
@app.route('/fitness', methods=['GET','POST'])
def fitness():
    if 'member_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        bmi = round(weight / (height/100)**2, 2) if height > 0 else 0
        fitness_level = request.form['fitness_level']

        c.execute("SELECT * FROM fitness_profile WHERE member_id=?", (session['member_id'],))
        existing = c.fetchone()
        if existing:
            c.execute("UPDATE fitness_profile SET height=?, weight=?, bmi=?, fitness_level=? WHERE member_id=?",
                      (height, weight, bmi, fitness_level, session['member_id']))
        else:
            c.execute("INSERT INTO fitness_profile (member_id, height, weight, bmi, fitness_level) VALUES (?,?,?,?,?)",
                      (session['member_id'], height, weight, bmi, fitness_level))
        conn.commit()

    c.execute("SELECT * FROM fitness_profile WHERE member_id=?", (session['member_id'],))
    profile = c.fetchone()
    conn.close()
    return render_template('fitness.html', profile=profile)

# ---------------- Membership Selection ----------------
@app.route('/membership', methods=['GET','POST'])
def membership():
    if 'member_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM membership_plans")
    plans = c.fetchall()

    if request.method == 'POST':
        selected_plan_id = request.form['plan_id']

        # Save or update membership
        c.execute("SELECT * FROM memberships WHERE member_id=?", (session['member_id'],))
        existing = c.fetchone()

        # Get duration of selected plan
        c.execute("SELECT duration_days FROM membership_plans WHERE id=?", (selected_plan_id,))
        duration = c.fetchone()['duration_days']

        if existing:
            c.execute("UPDATE memberships SET plan_id=?, start_date=date('now'), end_date=date('now','+{} days') WHERE member_id=?".format(duration),
                      (selected_plan_id, session['member_id']))
        else:
            c.execute("INSERT INTO memberships (member_id, plan_id, start_date, end_date) VALUES (?,?,date('now'), date('now','+{} days'))".format(duration),
                      (session['member_id'], selected_plan_id))
        conn.commit()
        flash("Membership plan selected successfully!", "success")
        return redirect('/membership_status')

    conn.close()
    return render_template('membership.html', plans=plans)

# ---------------- Membership Status ----------------
@app.route('/membership_status')
def membership_status():
    if 'member_id' not in session:
        return redirect('/login')

    member_id = session['member_id']
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT m.*, p.plan_name, p.duration_days 
        FROM memberships m
        JOIN membership_plans p ON m.plan_id=p.id
        WHERE m.member_id=?
    """, (member_id,))
    membership = c.fetchone()
    conn.close()

    if membership:
        today = datetime.today().date()
        end_date = datetime.strptime(membership['end_date'], "%Y-%m-%d").date()
        remaining_days = (end_date - today).days
        status = "Active" if remaining_days >= 0 else "Expired"
    else:
        membership = None
        remaining_days = None
        status = None

    return render_template('membership_status.html', membership=membership, status=status, remaining_days=remaining_days)

# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(debug=True, port=8080)