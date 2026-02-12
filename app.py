from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "smartsecretkey"

# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS polls(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        user_id INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS options(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        option_text TEXT,
        poll_id INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS votes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        poll_id INTEGER,
        option_id INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return redirect("/login")

# -------- REGISTER --------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO users(username,password) VALUES(?,?)",
                    (username, password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# -------- LOGIN --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            return redirect("/dashboard")

    return render_template("login.html")

# -------- DASHBOARD --------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM polls")
    polls = cur.fetchall()
    conn.close()

    return render_template("dashboard.html", polls=polls)

# -------- CREATE POLL --------
@app.route("/create_poll", methods=["GET", "POST"])
def create_poll():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        options = request.form.getlist("options")

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("INSERT INTO polls(title,user_id) VALUES(?,?)",
                    (title, session["user_id"]))
        poll_id = cur.lastrowid

        for option in options:
            if option.strip() != "":
                cur.execute("INSERT INTO options(option_text,poll_id) VALUES(?,?)",
                            (option, poll_id))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("create_poll.html")

# -------- VOTE --------
@app.route("/vote/<int:poll_id>", methods=["GET", "POST"])
def vote(poll_id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == "POST":
        option_id = request.form["option"]
        cur.execute("INSERT INTO votes(poll_id,option_id) VALUES(?,?)",
                    (poll_id, option_id))
        conn.commit()
        conn.close()
        return redirect(f"/results/{poll_id}")

    cur.execute("SELECT * FROM options WHERE poll_id=?", (poll_id,))
    options = cur.fetchall()
    conn.close()

    return render_template("vote.html", options=options, poll_id=poll_id)

# -------- RESULTS --------
@app.route("/results/<int:poll_id>")
def results(poll_id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT options.option_text, COUNT(votes.id)
        FROM options
        LEFT JOIN votes ON options.id = votes.option_id
        WHERE options.poll_id=?
        GROUP BY options.id
    """, (poll_id,))

    results = cur.fetchall()
    conn.close()

    return render_template("results.html", results=results)

# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
