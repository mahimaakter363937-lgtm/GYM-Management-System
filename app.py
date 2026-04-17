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
                "INSERT INTO members (name,phone,age,fitness_goal,username,password) VALUES (%s,%s,%s,%s,%s,%s)",
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
        member = conn.execute("SELECT * FROM members WHERE username=%s", (username,)).fetchone()
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

    conn = get_db()

    member = conn.execute(
        "SELECT * FROM members WHERE id=%s", 
        (session["member_id"],)
    ).fetchone()

    # 🔹 Fitness data
    fitness = conn.execute(
        "SELECT * FROM fitness_profile WHERE member_id=%s",
        (session["member_id"],)
    ).fetchone()

    # 🔹 Workout data
    workouts = conn.execute(
        "SELECT * FROM workouts WHERE member_id=%s ORDER BY id DESC",
        (session["member_id"],)
    ).fetchall()

    # 🔹 Diet plan
    diet = conn.execute("""
        SELECT dp.*
        FROM diet_plans dp
        JOIN member_diet_plans mdp ON dp.id = mdp.diet_plan_id
        WHERE mdp.member_id = %s
    """, (session["member_id"],)).fetchone()

    conn.close()

    return render_template(
        "dashboard.html",
        member=member,
        fitness=fitness,
        workouts=workouts,
        diet=diet
    )


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
            "UPDATE members SET name=%s,phone=%s,age=%s,fitness_goal=%s WHERE id=%s",
            (request.form["name"], request.form["phone"],
             request.form["age"], request.form["fitness_goal"],
             session["member_id"])
        )
        conn.commit()
        flash("Profile updated successfully!", "success")

    member = conn.execute("SELECT * FROM members WHERE id=%s", (session["member_id"],)).fetchone()
    conn.close()
    return render_template("profile.html", member=member)


# ==============================================================
#  FITNESS PROFILE (Updated By Richy)
# ==============================================================

from datetime import datetime


@app.route("/fitness", methods=["GET", "POST"])
def fitness():
    if "member_id" not in session:
        return redirect("/login")

    conn = get_db()

    if request.method == "POST":
        try:
            # Backend Validation: চেক করা হচ্ছে ইনপুট খালি কিনা
            height_str = request.form.get("height", "").strip()
            weight_str = request.form.get("weight", "").strip()
            fitness_level = request.form.get("fitness_level", "Beginner")

            if not height_str or not weight_str:
                flash("Height and Weight cannot be empty!", "danger")
                return redirect("/fitness")

            # String থেকে Float-এ কনভার্ট করা
            height = float(height_str)
            weight = float(weight_str)

            # 🔹 UPDATE: CM to Meters conversion (আগে এখানে Feet-এর লজিক ছিল)
            # BMI এর জন্য হাইট মিটারে হতে হয়। তাই (CM / 100) করা হয়েছে।
            height_in_meters = height / 100.0
            
            # BMI ক্যালকুলেশন: weight / height^2
            bmi = round(weight / (height_in_meters ** 2), 2) if height > 0 else 0

            # চেক করা হচ্ছে আগে প্রোফাইল তৈরি করা আছে কিনা
            existing = conn.execute(
                "SELECT * FROM fitness_profile WHERE member_id=%s", 
                (session["member_id"],)
            ).fetchone()

            if existing:
                conn.execute(
                    "UPDATE fitness_profile SET height=%s, weight=%s, bmi=%s, fitness_level=%s WHERE member_id=%s",
                    (height, weight, bmi, fitness_level, session["member_id"])
                )
            else:
                conn.execute(
                    "INSERT INTO fitness_profile (member_id, height, weight, bmi, fitness_level) VALUES (%s,%s,%s,%s,%s)",
                    (session["member_id"], height, weight, bmi, fitness_level)
                )

            # প্রগ্রেস হিস্ট্রি সেভ করা (যাতে ভবিষ্যতে গ্রাফ দেখানো যায়)
            conn.execute(
                "INSERT INTO progress (member_id, weight, bmi, date) VALUES (%s, %s, %s, %s)",
                (session["member_id"], weight, bmi, datetime.now().strftime("%Y-%m-%d"))
            )

            conn.commit()
            flash("Fitness metrics updated successfully!", "success")
        except Exception as e:
            flash(f"Invalid input: {e}", "danger")

    profile = conn.execute(
        "SELECT * FROM fitness_profile WHERE member_id=%s", 
        (session["member_id"],)
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
    plan = conn.execute("SELECT * FROM membership_plans WHERE id=%s", (plan_id,)).fetchone()
    conn.close()

    if not plan:
        flash("Plan not found.", "danger")
        return redirect("/membership")

    return render_template("checkout.html", plan=plan, stripe_public_key=STRIPE_PUBLIC_KEY)


# ==============================================================
#  PROCESS STRIPE PAYMENT (zadid)
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
    plan = conn.execute("SELECT * FROM membership_plans WHERE id=%s", (plan_id,)).fetchone()

    if not plan:
        flash("Invalid plan selected.", "danger")
        conn.close()
        return redirect("/membership")

    # ---------- Simulation: Always mark as Paid ----------
    payment_status = "Paid"
    print(f"DEBUG: Processing simulated payment for Plan {plan_id} with Card {card_number}")

    # ---------- Save payment record ----------
    today    = datetime.now()
    end_date = today + timedelta(days=plan["duration_days"])

    conn.execute(
        "INSERT INTO payments (member_id,plan_id,amount,payment_status,payment_date) VALUES (%s,%s,%s,%s,%s)",
        (session["member_id"], plan_id, plan["price"], payment_status, today.strftime("%Y-%m-%d"))
    )

    # Activate / update membership
    existing = conn.execute(
        "SELECT * FROM memberships WHERE member_id=%s", (session["member_id"],)
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE memberships SET plan_id=%s,start_date=%s,end_date=%s WHERE member_id=%s",
            (plan_id, today.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), session["member_id"])
        )
    else:
        conn.execute(
            "INSERT INTO memberships (member_id,plan_id,start_date,end_date) VALUES (%s,%s,%s,%s)",
            (session["member_id"], plan_id, today.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        )

    # ---------- Notify user: Payment success ----------
    success_msg = (
        f"✅ Payment Successful! You paid ${plan['price']:.2f} for the '{plan['plan_name']}' plan. "
        f"Your membership is active until {end_date.strftime('%Y-%m-%d')}."
    )
    conn.execute(
        "INSERT INTO notifications (member_id, message) VALUES (%s,%s)",
        (session["member_id"], success_msg)
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
        WHERE m.member_id = %s
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
        WHERE p.member_id = %s
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

    # Module 3 stats
    pending_feedback   = conn.execute("SELECT COUNT(*) FROM feedback WHERE status='Pending'").fetchone()[0]
    total_feedback     = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    pending_payments   = conn.execute("SELECT COUNT(*) FROM payments WHERE payment_status='Pending'").fetchone()[0]

    # Recent feedback (last 5) for dashboard preview
    recent_feedback = conn.execute("""
        SELECT f.*, m.name as member_name
        FROM feedback f
        JOIN members m ON f.member_id = m.id
        ORDER BY f.created_at DESC
        LIMIT 5
    """).fetchall()

    # Recent payments (last 5)
    recent_payments = conn.execute("""
        SELECT p.*, m.name as member_name, mp.plan_name
        FROM payments p
        JOIN members m ON p.member_id = m.id
        JOIN membership_plans mp ON p.plan_id = mp.id
        ORDER BY p.payment_date DESC
        LIMIT 5
    """).fetchall()

    total_diet_plans   = conn.execute("SELECT COUNT(*) FROM diet_plans").fetchone()[0]
    
    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_members    = total_members,
        total_plans      = total_plans,
        total_diet_plans = total_diet_plans,
        total_payments   = total_payments,
        total_revenue    = total_revenue,
        pending_feedback = pending_feedback,
        total_feedback   = total_feedback,
        pending_payments = pending_payments,
        recent_feedback  = recent_feedback,
        recent_payments  = recent_payments,
    )



# ==============================================================
#  ADMIN — MEMBER MANAGEMENT (Richy)
# ==============================================================
# --- MODULE 2: ADMIN MEMBER MANAGEMENT ---

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
                "INSERT INTO members (name,phone,age,fitness_goal,username,password) VALUES (%s,%s,%s,%s,%s,%s)",
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
    member = conn.execute("SELECT * FROM members WHERE id=%s", (id,)).fetchone()

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

        if not name:
            flash("Name cannot be empty!", "danger")
            return redirect(f"/admin/edit_member/{id}")

        if new_password:
            conn.execute(
                "UPDATE members SET name=%s,phone=%s,age=%s,fitness_goal=%s,password=%s WHERE id=%s",
                (name, phone, age, fitness_goal, generate_password_hash(new_password), id)
            )
        else:
            conn.execute(
                "UPDATE members SET name=%s,phone=%s,age=%s,fitness_goal=%s WHERE id=%s",
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
    member = conn.execute("SELECT name FROM members WHERE id=%s", (id,)).fetchone()
    if member:
        # মেম্বারের সাথে সংশ্লিষ্ট অন্যান্য ডাটাও মুছে ফেলা হচ্ছে
        conn.execute("DELETE FROM members WHERE id=%s", (id,))
        conn.execute("DELETE FROM fitness_profile WHERE member_id=%s", (id,))
        conn.execute("DELETE FROM memberships WHERE member_id=%s", (id,))
        conn.execute("DELETE FROM attendance WHERE member_id=%s", (id,))
        conn.execute("DELETE FROM workouts WHERE member_id=%s", (id,))
        conn.execute("DELETE FROM progress WHERE member_id=%s", (id,))
        conn.commit()
        flash(f"Member '{member['name']}' deleted.", "success")
    else:
        flash("Member not found.", "danger")
    conn.close()
    return redirect("/admin/members")

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
            "INSERT INTO membership_plans (plan_name,price,duration_days) VALUES (%s,%s,%s)",
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
    plan = conn.execute("SELECT * FROM membership_plans WHERE id=%s", (id,)).fetchone()

    if not plan:
        flash("Plan not found.", "danger")
        conn.close()
        return redirect("/admin/plans")

    if request.method == "POST":
        name     = request.form["plan_name"]
        price    = float(request.form["price"])
        duration = int(request.form["duration"])
        conn.execute(
            "UPDATE membership_plans SET plan_name=%s,price=%s,duration_days=%s WHERE id=%s",
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
    plan = conn.execute("SELECT plan_name FROM membership_plans WHERE id=%s", (id,)).fetchone()
    if plan:
        conn.execute("DELETE FROM membership_plans WHERE id=%s", (id,))
        conn.commit()
        flash(f"Plan '{plan['plan_name']}' deleted.", "success")
    else:
        flash("Plan not found.", "danger")
    conn.close()
    return redirect("/admin/plans")


# ==============================================================
#  ADMIN — PAYMENT HISTORY (Biva)
# ==============================================================
@app.route("/admin/payments")
def admin_payments():
    if admin_required():
        return redirect("/admin/login")

    conn = get_db()
    payments = conn.execute("""
        SELECT p.*, m.name, mp.plan_name
        FROM payments p
        JOIN members m ON p.member_id = m.id
        JOIN membership_plans mp ON p.plan_id = mp.id
        ORDER BY p.payment_date DESC
    """).fetchall()
    conn.close()
    return render_template("admin_payments.html", payments=payments)


@app.route("/admin/delete_payment/<int:id>")
def admin_delete_payment(id):
    if admin_required():
        return redirect("/admin/login")
    conn = get_db()
    conn.execute("DELETE FROM payments WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash("Payment record deleted.", "success")
    return redirect("/admin/payments")

@app.route("/admin/add_payment", methods=["GET", "POST"])
def admin_add_payment():
    if admin_required():
        return redirect("/admin/login")
    
    conn = get_db()
    
    if request.method == "POST":
        member_id = request.form["member_id"]
        plan_id   = request.form["plan_id"]
        amount    = float(request.form["amount"])
        status    = request.form["payment_status"]
        date      = request.form["payment_date"]
        
        # Save payment record
        conn.execute(
            "INSERT INTO payments (member_id,plan_id,amount,payment_status,payment_date) VALUES (%s,%s,%s,%s,%s)",
            (member_id, plan_id, amount, status, date)
        )
        
        # If Paid, update membership + notify user
        if status == "Paid":
            plan_info = conn.execute("SELECT duration_days, plan_name, price FROM membership_plans WHERE id=%s", (plan_id,)).fetchone()
            if plan_info:
                start_dt = datetime.strptime(date, "%Y-%m-%d")
                end_dt   = start_dt + timedelta(days=plan_info["duration_days"])

                existing = conn.execute("SELECT id FROM memberships WHERE member_id=%s", (member_id,)).fetchone()
                if existing:
                    conn.execute(
                        "UPDATE memberships SET plan_id=%s,start_date=%s,end_date=%s WHERE member_id=%s",
                        (plan_id, date, end_dt.strftime("%Y-%m-%d"), member_id)
                    )
                else:
                    conn.execute(
                        "INSERT INTO memberships (member_id,plan_id,start_date,end_date) VALUES (%s,%s,%s,%s)",
                        (member_id, plan_id, date, end_dt.strftime("%Y-%m-%d"))
                    )
                # Notify user: payment confirmed
                conn.execute(
                    "INSERT INTO notifications (member_id, message) VALUES (%s,%s)",
                    (member_id, f"✅ Payment of ${amount:.2f} for '{plan_info['plan_name']}' confirmed by Admin. Membership active until {end_dt.strftime('%Y-%m-%d')}.")
                )

        elif status == "Pending":
            plan_info = conn.execute("SELECT plan_name FROM membership_plans WHERE id=%s", (plan_id,)).fetchone()
            plan_label = plan_info["plan_name"] if plan_info else "your selected plan"
            # Notify user: payment pending
            conn.execute(
                "INSERT INTO notifications (member_id, message) VALUES (%s,%s)",
                (member_id, f"⏳ Payment of ${amount:.2f} for '{plan_label}' is PENDING. Please complete your payment to activate your membership.")
            )

        conn.commit()
        conn.close()
        flash("Payment record added successfully!", "success")
        return redirect("/admin/payments")


    members = conn.execute("SELECT id, name FROM members").fetchall()
    plans   = conn.execute("SELECT id, plan_name, price FROM membership_plans").fetchall()
    conn.close()
    return render_template("admin_add_payment.html", 
                         members=members, 
                         plans=plans, 
                         today=datetime.now().strftime("%Y-%m-%d"))


@app.route("/admin/edit_payment/<int:id>", methods=["GET", "POST"])
def admin_edit_payment(id):
    if admin_required():
        return redirect("/admin/login")
    
    conn = get_db()
    payment = conn.execute("SELECT * FROM payments WHERE id=%s", (id,)).fetchone()
    
    if not payment:
        flash("Payment not found.", "danger")
        conn.close()
        return redirect("/admin/payments")
        
    members = conn.execute("SELECT id, name FROM members").fetchall()
    plans   = conn.execute("SELECT id, plan_name FROM membership_plans").fetchall()

    if request.method == "POST":
        member_id = request.form["member_id"]
        plan_id   = request.form["plan_id"]
        amount    = float(request.form["amount"])
        status    = request.form["payment_status"]
        date      = request.form["payment_date"]
        
        conn.execute("""
            UPDATE payments 
            SET member_id=%s, plan_id=%s, amount=%s, payment_status=%s, payment_date=%s 
            WHERE id=%s
        """, (member_id, plan_id, amount, status, date, id))
        
        # If updated to Paid, update/activate membership
        if status == "Paid":
            plan = conn.execute("SELECT duration_days FROM membership_plans WHERE id=%s", (plan_id,)).fetchone()
            if plan:
                start_dt = datetime.strptime(date, "%Y-%m-%d")
                end_dt   = start_dt + timedelta(days=plan["duration_days"])
                
                existing = conn.execute("SELECT id FROM memberships WHERE member_id=%s", (member_id,)).fetchone()
                if existing:
                    conn.execute(
                        "UPDATE memberships SET plan_id=%s,start_date=%s,end_date=%s WHERE member_id=%s",
                        (plan_id, date, end_dt.strftime("%Y-%m-%d"), member_id)
                    )
                else:
                    conn.execute(
                        "INSERT INTO memberships (member_id,plan_id,start_date,end_date) VALUES (%s,%s,%s,%s)",
                        (member_id, plan_id, date, end_dt.strftime("%Y-%m-%d"))
                    )
        
        conn.commit()
        conn.close()
        flash("Payment record updated.", "success")
        return redirect("/admin/payments")
    
    conn.close()
    return render_template("admin_edit_payment.html", payment=payment, members=members, plans=plans)


# ==============================================================
#  MODULE 3 — NOTIFICATIONS (Biva)
# ==============================================================

def generate_expiry_notifications(member_id):
    """Auto-generate notifications for membership expiry."""
    conn = get_db()
    today = datetime.today().date()

    membership = conn.execute("""
        SELECT m.end_date, p.plan_name
        FROM memberships m
        JOIN membership_plans p ON m.plan_id = p.id
        WHERE m.member_id = %s
    """, (member_id,)).fetchone()

    if membership:
        end_date = datetime.strptime(membership["end_date"][:10], "%Y-%m-%d").date()
        days_left = (end_date - today).days

        # Only create notification if not already created today for same scenario
        if days_left == 7:
            msg = f"⚠️ Your '{membership['plan_name']}' membership expires in 7 days ({membership['end_date'][:10]}). Please renew soon!"
            existing = conn.execute(
                "SELECT id FROM notifications WHERE member_id=%s AND message=%s", (member_id, msg)
            ).fetchone()
            if not existing:
                conn.execute("INSERT INTO notifications (member_id, message) VALUES (%s,%s)", (member_id, msg))

        elif days_left == 3:
            msg = f"🚨 URGENT: Your '{membership['plan_name']}' membership expires in 3 days! Renew now to avoid losing access."
            existing = conn.execute(
                "SELECT id FROM notifications WHERE member_id=%s AND message=%s", (member_id, msg)
            ).fetchone()
            if not existing:
                conn.execute("INSERT INTO notifications (member_id, message) VALUES (%s,%s)", (member_id, msg))

        elif days_left == 0:
            msg = f"❌ Your '{membership['plan_name']}' membership expires TODAY! Please renew immediately."
            existing = conn.execute(
                "SELECT id FROM notifications WHERE member_id=%s AND message=%s", (member_id, msg)
            ).fetchone()
            if not existing:
                conn.execute("INSERT INTO notifications (member_id, message) VALUES (%s,%s)", (member_id, msg))

        elif days_left < 0:
            msg = f"❌ Your '{membership['plan_name']}' membership has EXPIRED {abs(days_left)} day(s) ago. Please renew to regain access."
            existing = conn.execute(
                "SELECT id FROM notifications WHERE member_id=%s AND message=%s", (member_id, msg)
            ).fetchone()
            if not existing:
                conn.execute("INSERT INTO notifications (member_id, message) VALUES (%s,%s)", (member_id, msg))

    conn.commit()
    conn.close()


@app.route("/notifications")
def notifications():
    if "member_id" not in session:
        return redirect("/login")

    generate_expiry_notifications(session["member_id"])

    conn = get_db()
    notifs = conn.execute(
        "SELECT * FROM notifications WHERE member_id=%s ORDER BY created_at DESC",
        (session["member_id"],)
    ).fetchall()
    conn.close()
    return render_template("notifications.html", notifications=notifs)


@app.route("/notifications/read/<int:id>")
def mark_notification_read(id):
    if "member_id" not in session:
        return redirect("/login")
    conn = get_db()
    conn.execute("UPDATE notifications SET is_read=1 WHERE id=%s AND member_id=%s", (id, session["member_id"]))
    conn.commit()
    conn.close()
    return redirect("/notifications")


@app.route("/notifications/read_all")
def mark_all_read():
    if "member_id" not in session:
        return redirect("/login")
    conn = get_db()
    conn.execute("UPDATE notifications SET is_read=1 WHERE member_id=%s", (session["member_id"],))
    conn.commit()
    conn.close()
    flash("All notifications marked as read.", "success")
    return redirect("/notifications")


# ==============================================================
#  MODULE 3 — FEEDBACK / COMPLAINTS (Biva)
# ==============================================================

@app.route("/feedback", methods=["GET", "POST"])
def submit_feedback():
    if "member_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        subject = request.form["subject"].strip()
        message = request.form["message"].strip()
        if not subject or not message:
            flash("Subject and message are required.", "danger")
            return redirect("/feedback")
        conn = get_db()
        conn.execute(
            "INSERT INTO feedback (member_id, subject, message) VALUES (%s,%s,%s)",
            (session["member_id"], subject, message)
        )
        conn.commit()
        conn.close()
        flash("Your feedback has been submitted successfully!", "success")
        return redirect("/dashboard")

    conn = get_db()
    my_feedback = conn.execute(
        "SELECT * FROM feedback WHERE member_id=%s ORDER BY created_at DESC",
        (session["member_id"],)
    ).fetchall()
    conn.close()
    return render_template("feedback.html", my_feedback=my_feedback)


# Admin: view all feedback
@app.route("/admin/feedback")
def admin_feedback():
    if admin_required():
        return redirect("/admin/login")
    conn = get_db()
    feedbacks = conn.execute("""
        SELECT f.*, m.name as member_name
        FROM feedback f
        JOIN members m ON f.member_id = m.id
        ORDER BY f.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("admin_feedback.html", feedbacks=feedbacks)


# Admin: reply to feedback
@app.route("/admin/feedback/reply/<int:id>", methods=["GET", "POST"])
def admin_reply_feedback(id):
    if admin_required():
        return redirect("/admin/login")

    conn = get_db()
    fb = conn.execute("""
        SELECT f.*, m.name as member_name
        FROM feedback f
        JOIN members m ON f.member_id = m.id
        WHERE f.id=%s
    """, (id,)).fetchone()

    if not fb:
        flash("Feedback not found.", "danger")
        conn.close()
        return redirect("/admin/feedback")

    if request.method == "POST":
        reply = request.form["admin_reply"].strip()
        conn.execute(
            "UPDATE feedback SET admin_reply=%s, status='Resolved' WHERE id=%s",
            (reply, id)
        )

        # ✅ Notify the member that admin replied to their feedback
        notif_msg = (
            f"💬 Admin replied to your feedback: \"{fb['subject']}\". "
            f"Reply: \"{reply}\". Visit Feedback section to view the full response."
        )
        conn.execute(
            "INSERT INTO notifications (member_id, message) VALUES (%s,%s)",
            (fb["member_id"], notif_msg)
        )

        conn.commit()
        conn.close()
        flash("Reply sent successfully! Member has been notified.", "success")
        return redirect("/admin/feedback")


    conn.close()
    return render_template("admin_reply_feedback.html", fb=fb)


# ==============================================================
#  DIET PLANS (Mahima)
# ==============================================================

@app.route("/my_diet")
def my_diet():
    if "member_id" not in session:
        return redirect("/login")
    
    conn = get_db()
    diet = conn.execute("""
        SELECT dp.* 
        FROM diet_plans dp
        JOIN member_diet_plans mdp ON dp.id = mdp.diet_plan_id
        WHERE mdp.member_id = %s
    """, (session["member_id"],)).fetchone()
    conn.close()
    return render_template("my_diet.html", diet=diet)

@app.route("/admin/diet_plans")
def admin_diet_plans():
    if admin_required():
        return redirect("/admin/login")
    conn = get_db()
    plans = conn.execute("SELECT * FROM diet_plans ORDER BY name").fetchall()
    conn.close()
    return render_template("admin_diet_plans.html", plans=plans)

@app.route("/admin/add_diet_plan", methods=["GET", "POST"])
def admin_add_diet_plan():
    if admin_required():
        return redirect("/admin/login")
    
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        fitness_goal = request.form["fitness_goal"]
        
        conn = get_db()
        conn.execute(
            "INSERT INTO diet_plans (name, description, fitness_goal) VALUES (%s,%s,%s)",
            (name, description, fitness_goal)
        )
        conn.commit()
        conn.close()
        flash(f"Diet plan '{name}' created!", "success")
        return redirect("/admin/diet_plans")
    
    return render_template("admin_add_diet_plan.html")

@app.route("/admin/edit_diet_plan/<int:id>", methods=["GET", "POST"])
def admin_edit_diet_plan(id):
    if admin_required():
        return redirect("/admin/login")
    
    conn = get_db()
    plan = conn.execute("SELECT * FROM diet_plans WHERE id=%s", (id,)).fetchone()
    
    if not plan:
        flash("Diet plan not found.", "danger")
        conn.close()
        return redirect("/admin/diet_plans")

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        fitness_goal = request.form["fitness_goal"]
        
        conn.execute(
            "UPDATE diet_plans SET name=%s, description=%s, fitness_goal=%s WHERE id=%s",
            (name, description, fitness_goal, id)
        )
        conn.commit()
        conn.close()
        flash(f"Diet plan '{name}' updated!", "success")
        return redirect("/admin/diet_plans")
    
    conn.close()
    return render_template("admin_add_diet_plan.html", plan=plan)

@app.route("/admin/delete_diet_plan/<int:id>")
def admin_delete_diet_plan(id):
    if admin_required():
        return redirect("/admin/login")
    conn = get_db()
    conn.execute("DELETE FROM diet_plans WHERE id=%s", (id,))
    conn.execute("DELETE FROM member_diet_plans WHERE diet_plan_id=%s", (id,))
    conn.commit()
    conn.close()
    flash("Diet plan deleted.", "success")
    return redirect("/admin/diet_plans")

@app.route("/admin/assign_diet", methods=["GET", "POST"])
@app.route("/admin/assign_diet/<int:pre_member_id>", methods=["GET", "POST"])
def admin_assign_diet(pre_member_id=None):
    if admin_required():
        return redirect("/admin/login")
    
    conn = get_db()
    if request.method == "POST":
        member_id = request.form["member_id"]
        diet_plan_id = request.form["diet_plan_id"]
        
        # 🔹 SQLite এর 'INSERT OR REPLACE' এর বদলে PostgreSQL ফ্রেন্ডলি লজিক (ON CONFLICT)
        conn.execute("""
            INSERT INTO member_diet_plans (member_id, diet_plan_id) 
            VALUES (%s, %s)
            ON CONFLICT (member_id) 
            DO UPDATE SET diet_plan_id = EXCLUDED.diet_plan_id
        """, (member_id, diet_plan_id))
        
        # Notify user
        plan_name = conn.execute("SELECT name FROM diet_plans WHERE id=%s", (diet_plan_id,)).fetchone()["name"]
        conn.execute("INSERT INTO notifications (member_id, message) VALUES (%s,%s)", 
                     (member_id, f"🥗 Admin has assigned a new diet plan to you: {plan_name}. Check 'My Diet' for details!"))
        
        conn.commit()
        flash("Diet plan assigned successfully!", "success")
        return redirect("/admin")

    members = conn.execute("SELECT id, name, fitness_goal FROM members").fetchall()
    diet_plans = conn.execute("SELECT id, name, fitness_goal FROM diet_plans").fetchall()
    
    # Fetch current assignments
    assignments = conn.execute("""
        SELECT mdp.id, m.name as member_name, dp.name as plan_name, mdp.assigned_at
        FROM member_diet_plans mdp
        JOIN members m ON mdp.member_id = m.id
        JOIN diet_plans dp ON mdp.diet_plan_id = dp.id
        ORDER BY mdp.assigned_at DESC
    """).fetchall()
    
    conn.close()
    return render_template("admin_assign_diet.html", 
                           members=members, 
                           diet_plans=diet_plans, 
                           pre_member_id=pre_member_id,
                           assignments=assignments)

@app.route("/admin/delete_assigned_diet/<int:id>")
def admin_delete_assigned_diet(id):
    if admin_required():
        return redirect("/admin/login")
    conn = get_db()
    conn.execute("DELETE FROM member_diet_plans WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash("Diet assignment removed.", "success")
    return redirect("/admin/assign_diet")



# ==============================================================
#  Richy- MODULE-3 
# ============================================================
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
        db.execute('DELETE FROM attendance WHERE date = %s', (target_date,))
        
        members_list = db.execute('SELECT id FROM members').fetchall()
        for m in members_list:
            status = request.form.get(f'status_{m["id"]}')
            if status == 'Present':
                db.execute('INSERT INTO attendance (member_id, status, date) VALUES (%s, %s, %s)',
                           (m['id'], 'Present', target_date))
        
        db.commit()
        flash(f'Attendance successfully saved for {target_date}!', 'success')
        # সেভ করার পর ওই তারিখের পেজেই রিডাইরেক্ট করবে
        return redirect(f'/admin/attendance%sdate={target_date}')

    members = db.execute('SELECT id, name, phone FROM members').fetchall()
    
    # সিলেক্টেড ডেটের প্রেজেন্ট মেম্বারদের আইডি বের করা হচ্ছে
    today_attendance = db.execute('SELECT member_id FROM attendance WHERE date = %s AND status = "Present"', (selected_date,)).fetchall()
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
        
        db.execute('INSERT INTO workouts (member_id, workout_type, schedule_details) VALUES (%s, %s, %s)',
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
    db.execute('DELETE FROM workouts WHERE id = %s', (id,))
    db.commit()
    flash('Workout plan removed.', 'info')
    return redirect('/admin/assign_workout')








@app.route('/admin/edit_workout/<int:id>', methods=['GET', 'POST'])
def admin_edit_workout(id):
    if not session.get('admin'):
        return redirect('/admin/login')
    
    db = get_db()
    workout = db.execute('SELECT * FROM workouts WHERE id = %s', (id,)).fetchone()
    
    if not workout:
        flash('Workout not found!', 'danger')
        return redirect('/admin/assign_workout')
    
    if request.method == 'POST':
        workout_type = request.form.get('workout_type')
        schedule_details = request.form.get('schedule_details')
        
        db.execute('''
            UPDATE workouts 
            SET workout_type = %s, schedule_details = %s 
            WHERE id = %s
        ''', (workout_type, schedule_details, id))
        db.commit()
        flash('Workout updated successfully!', 'success')
        return redirect('/admin/assign_workout')

    return render_template('admin_edit_workout.html', workout=workout)





# ==============================================================
#  MY WORKOUT (Zadid)
# ==============================================================
@app.route("/my_workouts")
def my_workouts():
    if "member_id" not in session:
        return redirect("/login")

    conn = get_db()
    workouts = conn.execute(
        "SELECT * FROM workouts WHERE member_id=%s ORDER BY id DESC",
        (session["member_id"],)
    ).fetchall()
    conn.close()

    return render_template("my_workouts.html", workouts=workouts)

# ==============================================================
#  Fitness Progress (Zadid)
# ==============================================================
@app.route("/my_fitness")
def my_fitness():
    if "member_id" not in session:
        return redirect("/login")

    conn = get_db()

    # 🔹 Current fitness
    fitness = conn.execute(
        "SELECT * FROM fitness_profile WHERE member_id=%s",
        (session["member_id"],)
    ).fetchone()

    # 🔥 NEW: Progress history
    progress = conn.execute(
        "SELECT * FROM progress WHERE member_id=%s ORDER BY date",
        (session["member_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "my_fitness.html",
        fitness=fitness,
        progress=progress
    )



# ==============================================================
#  RUN
# ==============================================================
import os

if __name__ == "__main__":
    # Render অটোমেটিক পোর্ট সেট করে, তাই এটি ব্যবহার করা জরুরি
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host='0.0.0.0', port=port)
