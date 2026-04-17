from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import stripe
import os

app = Flask(__name__)
app.secret_key = "gym_elite_secret_2024"

# ---------------------------------------------------------------
# Stripe Configuration
# Use test keys — replace with live keys in production
# ---------------------------------------------------------------
STRIPE_PUBLIC_KEY  = "pk_test_51000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
STRIPE_SECRET_KEY  = "sk_test_51000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
stripe.api_key = STRIPE_SECRET_KEY

# ---------------------------------------------------------------
# Admin Credentials (hardcoded — can be moved to DB later)
# ---------------------------------------------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# ---------------------------------------------------------------
# DATABASE HELPER
# ---------------------------------------------------------------
from flask import Flask, render_template, request, redirect, session, flash
import os
import psycopg2
import psycopg2.extras
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import stripe
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# ---------------------------------------------------------------
# Stripe & Admin Configuration
# ---------------------------------------------------------------
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# ---------------------------------------------------------------
# HYBRID DATABASE HELPER (SQLite + PostgreSQL)
# ---------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    if DATABASE_URL:
        # PostgreSQL কানেকশন (Render/Cloud এর জন্য)
        url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        # RealDictCursor ব্যবহার করা হয়েছে যাতে row["column_name"] এভাবে ডেটা পড়া যায়
        conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = True 
        return conn
    else:
        # লোকাল কম্পিউটারে কাজ করার সময় SQLite কানেকশন
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn


# ==============================================================
#  HOME
# ==============================================================
@app.route("/")
def home():
    return render_template("index.html")


# ==============================================================
#  MEMBER AUTH
# ==============================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name         = request.form["name"]
        phone        = request.form["phone"]
        age          = request.form["age"]
        fitness_goal = request.form["fitness_goal"]
        username     = request.form["username"]
        password     = generate_password_hash(request.form["password"])

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO members (name,phone,age,fitness_goal,username,password) VALUES (?,?,?,?,?,?)",
                (name, phone, age, fitness_goal, username, password)
            )
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect("/login")
        except sqlite3.IntegrityError:
            flash("Username already taken. Please choose another.", "danger")
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        # Check if this is the admin first
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            flash("Welcome, Admin! 👑", "success")
            return redirect("/admin")

        # Otherwise check member database
        conn   = get_db()
        member = conn.execute("SELECT * FROM members WHERE username=?", (username,)).fetchone()
        conn.close()

        if member and check_password_hash(member["password"], password):
            session["member_id"] = member["id"]
            flash(f"Welcome back, {member['name']}! 💪", "success")
            return redirect("/dashboard")

        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ==============================================================
#  MEMBER DASHBOARD
# ==============================================================
@app.route("/dashboard")
def dashboard():
    if "member_id" not in session:
        return redirect("/login")
    conn   = get_db()
    member = conn.execute("SELECT * FROM members WHERE id=?", (session["member_id"],)).fetchone()
    conn.close()
    return render_template("dashboard.html", member=member)


# ==============================================================
#  MEMBER PROFILE
# ==============================================================
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "member_id" not in session:
        return redirect("/login")

    conn = get_db()
    if request.method == "POST":
        conn.execute(
            "UPDATE members SET name=?,phone=?,age=?,fitness_goal=? WHERE id=?",
            (request.form["name"], request.form["phone"],
             request.form["age"], request.form["fitness_goal"],
             session["member_id"])
        )
        conn.commit()
        flash("Profile updated successfully!", "success")

    member = conn.execute("SELECT * FROM members WHERE id=?", (session["member_id"],)).fetchone()
    conn.close()
    return render_template("profile.html", member=member)


# ==============================================================
#  FITNESS PROFILE
# ==============================================================
@app.route("/fitness", methods=["GET", "POST"])
def fitness():
    if "member_id" not in session:
        return redirect("/login")

    conn = get_db()
    if request.method == "POST":
        height        = float(request.form["height"])
        weight        = float(request.form["weight"])
        fitness_level = request.form["fitness_level"]
        bmi           = round(weight / ((height / 100) ** 2), 2) if height > 0 else 0

        existing = conn.execute(
            "SELECT * FROM fitness_profile WHERE member_id=?", (session["member_id"],)
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE fitness_profile SET height=?,weight=?,bmi=?,fitness_level=? WHERE member_id=?",
                (height, weight, bmi, fitness_level, session["member_id"])
            )
        else:
            conn.execute(
                "INSERT INTO fitness_profile (member_id,height,weight,bmi,fitness_level) VALUES (?,?,?,?,?)",
                (session["member_id"], height, weight, bmi, fitness_level)
            )
        conn.commit()
        flash("Fitness metrics updated!", "success")

    profile = conn.execute(
        "SELECT * FROM fitness_profile WHERE member_id=?", (session["member_id"],)
    ).fetchone()
    conn.close()
    return render_template("fitness.html", profile=profile)


# ==============================================================
#  MEMBERSHIP — PLAN SELECTION
# ==============================================================
@app.route("/membership", methods=["GET", "POST"])
def membership():
    if "member_id" not in session:
        return redirect("/login")

    conn  = get_db()
    plans = conn.execute("SELECT * FROM membership_plans").fetchall()
    conn.close()

    if request.method == "POST":
        plan_id = request.form.get("plan_id")
        if not plan_id:
            flash("Please select a plan.", "warning")
            return redirect("/membership")
        # Redirect to checkout page with selected plan
        return redirect(f"/checkout/{plan_id}")

    return render_template("membership.html", plans=plans)


# ==============================================================
#  CHECKOUT — STRIPE PAYMENT
# ==============================================================
@app.route("/checkout/<int:plan_id>")
def checkout(plan_id):
    if "member_id" not in session:
        return redirect("/login")

    conn = get_db()
    plan = conn.execute("SELECT * FROM membership_plans WHERE id=?", (plan_id,)).fetchone()
    conn.close()

    if not plan:
        flash("Plan not found.", "danger")
        return redirect("/membership")

    return render_template("checkout.html", plan=plan, stripe_public_key=STRIPE_PUBLIC_KEY)


# ==============================================================
#  PROCESS STRIPE PAYMENT
# ==============================================================
@app.route("/process_payment", methods=["POST"])
def process_payment():
    if "member_id" not in session:
        return redirect("/login")

    plan_id = request.form.get("plan_id")
    # We no longer need the stripeToken since we are allowing any card info
    card_number = request.form.get("card_number")
    cvc = request.form.get("cvc")

    conn = get_db()
    plan = conn.execute("SELECT * FROM membership_plans WHERE id=?", (plan_id,)).fetchone()

    if not plan:
        flash("Invalid plan selected.", "danger")
        conn.close()
        return redirect("/membership")

    # ---------- Simulation: Always mark as Paid ----------
    payment_status = "Paid"
    
    # In a real app involving Stripe, we would call Stripe API here.
    # But as per user request, we accept any random details.
    print(f"DEBUG: Processing simulated payment for Plan {plan_id} with Card {card_number}")

    # ---------- Save payment record ----------
    today    = datetime.now()
    end_date = today + timedelta(days=plan["duration_days"])

    conn.execute(
        "INSERT INTO payments (member_id,plan_id,amount,payment_status,payment_date) VALUES (?,?,?,?,?)",
        (session["member_id"], plan_id, plan["price"], payment_status, today.strftime("%Y-%m-%d"))
    )

    # Activate / update membership
    existing = conn.execute(
        "SELECT * FROM memberships WHERE member_id=?", (session["member_id"],)
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE memberships SET plan_id=?,start_date=?,end_date=? WHERE member_id=?",
            (plan_id, today.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), session["member_id"])
        )
    else:
        conn.execute(
            "INSERT INTO memberships (member_id,plan_id,start_date,end_date) VALUES (?,?,?,?)",
            (session["member_id"], plan_id, today.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        )

    conn.commit()
    conn.close()

    return render_template(
        "payment_success.html",
        plan_name = plan["plan_name"],
        amount    = f"{plan['price']:.2f}",
        date      = today.strftime("%B %d, %Y")
    )


# ==============================================================
#  MEMBERSHIP STATUS
# ==============================================================
@app.route("/membership_status")
def membership_status():
    if "member_id" not in session:
        return redirect("/login")

    conn = get_db()
    membership = conn.execute("""
        SELECT m.*, p.plan_name, p.duration_days
        FROM memberships m
        JOIN membership_plans p ON m.plan_id = p.id
        WHERE m.member_id = ?
    """, (session["member_id"],)).fetchone()
    conn.close()

    remaining_days = None
    status = None
    if membership:
        today          = datetime.today().date()
        end_date       = datetime.strptime(membership["end_date"][:10], "%Y-%m-%d").date()
        remaining_days = (end_date - today).days
        status         = "Active" if remaining_days >= 0 else "Expired"

    return render_template(
        "membership_status.html",
        membership     = membership,
        status         = status,
        remaining_days = remaining_days
    )


# ==============================================================
#  USER PAYMENT HISTORY
# ==============================================================
@app.route("/payment_history")
def payment_history():
    if "member_id" not in session:
        return redirect("/login")

    conn = get_db()
    payments = conn.execute("""
        SELECT p.*, mp.plan_name
        FROM payments p
        JOIN membership_plans mp ON p.plan_id = mp.id
        WHERE p.member_id = ?
        ORDER BY p.payment_date DESC
    """, (session["member_id"],)).fetchall()
    conn.close()
    return render_template("payment_history.html", payments=payments)


# ==============================================================
#  ADMIN AUTH
# ==============================================================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        if (username == ADMIN_USERNAME and
                password == ADMIN_PASSWORD):
            session["admin"] = True
            flash("Welcome, Admin! 👑", "success")
            return redirect("/admin")
        flash("Invalid admin credentials.", "danger")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/")


def admin_required():
    return "admin" not in session


# ==============================================================
#  ADMIN DASHBOARD
# ==============================================================
@app.route("/admin")
def admin_dashboard():
    if admin_required():
        return redirect("/admin/login")

    conn           = get_db()
    total_members  = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    total_plans    = conn.execute("SELECT COUNT(*) FROM membership_plans").fetchone()[0]
    total_payments = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
    rev_row        = conn.execute("SELECT SUM(amount) FROM payments WHERE payment_status='Paid'").fetchone()[0]
    total_revenue  = rev_row if rev_row else 0.0
    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_members  = total_members,
        total_plans    = total_plans,
        total_payments = total_payments,
        total_revenue  = total_revenue
    )

# ==============================================================
#  ADMIN — MEMBERSHIP PLAN MANAGEMENT (Mahima)
# ==============================================================
@app.route("/admin/plans")
def admin_plans():
    if admin_required():
        return redirect("/admin/login")
    conn  = get_db()
    plans = conn.execute("SELECT * FROM membership_plans ORDER BY price").fetchall()
    conn.close()
    return render_template("admin_plans.html", plans=plans)


@app.route("/admin/add_plan", methods=["GET", "POST"])
def admin_add_plan():
    if admin_required():
        return redirect("/admin/login")

    if request.method == "POST":
        name     = request.form["plan_name"]
        price    = float(request.form["price"])
        duration = int(request.form["duration"])

        conn = get_db()
        conn.execute(
            "INSERT INTO membership_plans (plan_name,price,duration_days) VALUES (?,?,?)",
            (name, price, duration)
        )
        conn.commit()
        conn.close()
        flash(f"Plan '{name}' created successfully!", "success")
        return redirect("/admin/plans")

    return render_template("add_plan.html")


@app.route("/admin/edit_plan/<int:id>", methods=["GET", "POST"])
def admin_edit_plan(id):
    if admin_required():
        return redirect("/admin/login")

    conn = get_db()
    plan = conn.execute("SELECT * FROM membership_plans WHERE id=?", (id,)).fetchone()

    if not plan:
        flash("Plan not found.", "danger")
        conn.close()
        return redirect("/admin/plans")

    if request.method == "POST":
        name     = request.form["plan_name"]
        price    = float(request.form["price"])
        duration = int(request.form["duration"])
        conn.execute(
            "UPDATE membership_plans SET plan_name=?,price=?,duration_days=? WHERE id=?",
            (name, price, duration, id)
        )
        conn.commit()
        conn.close()
        flash(f"Plan '{name}' updated successfully!", "success")
        return redirect("/admin/plans")

    conn.close()
    return render_template("admin_edit_plan.html", plan=plan)


@app.route("/admin/delete_plan/<int:id>")
def admin_delete_plan(id):
    if admin_required():
        return redirect("/admin/login")

    conn = get_db()
    plan = conn.execute("SELECT plan_name FROM membership_plans WHERE id=?", (id,)).fetchone()
    if plan:
        conn.execute("DELETE FROM membership_plans WHERE id=?", (id,))
        conn.commit()
        flash(f"Plan '{plan['plan_name']}' deleted.", "success")
    else:
        flash("Plan not found.", "danger")
    conn.close()
    return redirect("/admin/plans") 

    
#👍  ADMIN — MEMBER MANAGEMENTS by (Richy)

@app.route("/admin/members")
def admin_members():
    if admin_required():
        return redirect("/admin/login")
    conn = get_db()
    members = conn.execute("SELECT * FROM members ORDER BY name").fetchall()
    conn.close()
    return render_template("admin_members.html", members=members)


@app.route("/admin/add_member", methods=["GET", "POST"])
def admin_add_member():
    if admin_required():
        return redirect("/admin/login")

    if request.method == "POST":
        # .strip() ব্যবহার করা হয়েছে যাতে শুধু স্পেস দিয়ে কেউ ফর্ম পূরণ করতে না পারে
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        age = request.form.get("age", "").strip()
        fitness_goal = request.form.get("fitness_goal", "")
        username = request.form.get("username", "").strip()
        password_raw = request.form.get("password", "").strip()

        # 🔹 ব্যাকএন্ড ভ্যালিডেশন: নাম, ইউজারনেম এবং পাসওয়ার্ড খালি আছে কিনা চেক
        if not name or not username or not password_raw:
            flash("Required fields (Name, Username, Password) cannot be empty!", "danger")
            return redirect("/admin/add_member")

        password = generate_password_hash(password_raw)
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO members (name,phone,age,fitness_goal,username,password) VALUES (?,?,?,?,?,?)",
                (name, phone, age, fitness_goal, username, password)
            )
            conn.commit()
            flash(f"Member '{name}' added successfully!", "success")
            return redirect("/admin/members")
        except sqlite3.IntegrityError:
            flash("Username already exists.", "danger")
        finally:
            conn.close()

    return render_template("admin_add_member.html")


@app.route("/admin/edit_member/<int:id>", methods=["GET", "POST"])
def admin_edit_member(id):
    if admin_required():
        return redirect("/admin/login")

    conn = get_db()
    member = conn.execute("SELECT * FROM members WHERE id=?", (id,)).fetchone()

    if not member:
        flash("Member not found.", "danger")
        conn.close()
        return redirect("/admin/members")

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        age = request.form.get("age", "").strip()
        fitness_goal = request.form.get("fitness_goal", "")
        new_password = request.form.get("password", "").strip()

        # 🔹 ব্যাকএন্ড ভ্যালিডেশন: এডিট করার সময় নাম খালি রাখা যাবে না
        if not name:
            flash("Name cannot be empty!", "danger")
            return redirect(f"/admin/edit_member/{id}")

        if new_password:
            conn.execute(
                "UPDATE members SET name=?,phone=?,age=?,fitness_goal=?,password=? WHERE id=?",
                (name, phone, age, fitness_goal, generate_password_hash(new_password), id)
            )
        else:
            conn.execute(
                "UPDATE members SET name=?,phone=?,age=?,fitness_goal=? WHERE id=?",
                (name, phone, age, fitness_goal, id)
            )
        conn.commit()
        conn.close()
        flash(f"Member '{name}' updated successfully!", "success")
        return redirect("/admin/members")

    conn.close()
    return render_template("admin_edit_member.html", member=member)


@app.route("/admin/delete_member/<int:id>")
def admin_delete_member(id):
    if admin_required():
        return redirect("/admin/login")

    conn = get_db()
    member = conn.execute("SELECT name FROM members WHERE id=?", (id,)).fetchone()
    if member:
        # মেম্বারের সাথে সংশ্লিষ্ট অন্যান্য ডাটাও মুছে ফেলা হচ্ছে
        conn.execute("DELETE FROM members WHERE id=?", (id,))
        conn.execute("DELETE FROM fitness_profile WHERE member_id=?", (id,))
        conn.execute("DELETE FROM memberships WHERE member_id=?", (id,))
        conn.execute("DELETE FROM attendance WHERE member_id=?", (id,))
        conn.execute("DELETE FROM workouts WHERE member_id=?", (id,))
        conn.execute("DELETE FROM progress WHERE member_id=?", (id,))
        conn.commit()
        flash(f"Member '{member['name']}' deleted.", "success")
    else:
        flash("Member not found.", "danger")
    conn.close()
    return redirect("/admin/members")


@app.route("/admin/edit_member/<int:id>", methods=["GET", "POST"])
def admin_edit_member(id):
    if admin_required():
        return redirect("/admin/login")

    conn   = get_db()
    member = conn.execute("SELECT * FROM members WHERE id=?", (id,)).fetchone()

    if not member:
        flash("Member not found.", "danger")
        conn.close()
        return redirect("/admin/members")

    if request.method == "POST":
        name         = request.form["name"]
        phone        = request.form["phone"]
        age          = request.form["age"]
        fitness_goal = request.form["fitness_goal"]
        new_password = request.form.get("password", "").strip()

        if new_password:
            conn.execute(
                "UPDATE members SET name=?,phone=?,age=?,fitness_goal=?,password=? WHERE id=?",
                (name, phone, age, fitness_goal, generate_password_hash(new_password), id)
            )
        else:
            conn.execute(
                "UPDATE members SET name=?,phone=?,age=?,fitness_goal=? WHERE id=?",
                (name, phone, age, fitness_goal, id)
            )
        conn.commit()
        conn.close()
        flash(f"Member '{name}' updated successfully!", "success")
        return redirect("/admin/members")

    conn.close()
    return render_template("admin_edit_member.html", member=member)

from datetime import date

# --- MODULE 3: ATTENDANCE & WORKOUTS (Richy) ---
@app.route('/admin/attendance', methods=['GET', 'POST'])
def admin_attendance():
    if not session.get('admin'): return redirect('/admin/login')
    db = get_db()
    
    # 🔹 Dynamic Date Fix: URL থেকে ডেট নিবে, না থাকলে আজকের ডেট নিবে
    selected_date = request.args.get('date', date.today().isoformat())
    
    if request.method == 'POST':
        # ফর্ম থেকে হিডেন ইনপুট হিসেবে সিলেক্টেড ডেট নিয়ে আসা হচ্ছে
        target_date = request.form.get('attendance_date', selected_date)
        
        # আগে এই তারিখের যা এটেন্ডেন্স ছিল তা ডিলিট করা হচ্ছে যাতে ডুপ্লিকেট না হয়
        db.execute('DELETE FROM attendance WHERE date = ?', (target_date,))
        
        members_list = db.execute('SELECT id FROM members').fetchall()
        for m in members_list:
            status = request.form.get(f'status_{m["id"]}')
            if status == 'Present':
                db.execute('INSERT INTO attendance (member_id, status, date) VALUES (?, ?, ?)',
                           (m['id'], 'Present', target_date))
        
        db.commit()
        flash(f'Attendance successfully saved for {target_date}!', 'success')
        # সেভ করার পর ওই তারিখের পেজেই রিডাইরেক্ট করবে
        return redirect(f'/admin/attendance?date={target_date}')

    members = db.execute('SELECT id, name, phone FROM members').fetchall()
    
    # সিলেক্টেড ডেটের প্রেজেন্ট মেম্বারদের আইডি বের করা হচ্ছে
    today_attendance = db.execute('SELECT member_id FROM attendance WHERE date = ? AND status = "Present"', (selected_date,)).fetchall()
    present_ids = [row['member_id'] for row in today_attendance]
    
    history = db.execute('''
        SELECT date, COUNT(member_id) as total_present 
        FROM attendance 
        WHERE status = 'Present'
        GROUP BY date 
        ORDER BY date DESC 
        LIMIT 5
    ''').fetchall()
    
    return render_template('admin_attendance.html', 
                           members=members, 
                           selected_date=selected_date, # Updated variable name
                           present_ids=present_ids, 
                           history=history)

# Workout Routes (আগের মতোই, শুধু delete_workout অ্যাড করা হয়েছে)
@app.route('/admin/assign_workout', methods=['GET', 'POST'])
def admin_assign_workout():
    if not session.get('admin'): return redirect('/admin/login')
    db = get_db()
    
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        workout_type = request.form.get('workout_type')
        schedule_details = request.form.get('schedule_details')
        
        db.execute('INSERT INTO workouts (member_id, workout_type, schedule_details) VALUES (?, ?, ?)',
                   (member_id, workout_type, schedule_details))
        db.commit()
        flash('Workout assigned successfully!', 'success')
        return redirect('/admin/assign_workout')

    members = db.execute('''
        SELECT m.id, m.name, COALESCE(m.fitness_goal, 'General') as goal, COALESCE(fp.fitness_level, 'Beginner') as level
        FROM members m LEFT JOIN fitness_profile fp ON m.id = fp.member_id ORDER BY m.name ASC
    ''').fetchall()

    workouts = db.execute('''
        SELECT w.*, m.name as member_name 
        FROM workouts w JOIN members m ON w.member_id = m.id ORDER BY w.id DESC
    ''').fetchall()

    return render_template('admin_assign_workout.html', members=members, workouts=workouts)

@app.route('/admin/delete_workout/<int:id>')
def admin_delete_workout(id):
    if not session.get('admin'): return redirect('/admin/login')
    db = get_db()
    db.execute('DELETE FROM workouts WHERE id = ?', (id,))
    db.commit()
    flash('Workout plan removed.', 'info')
    return redirect('/admin/assign_workout')
    
# ==============================================================
#  RUN
# ==============================================================
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
