import os
from contextlib import contextmanager

import psycopg2
import psycopg2.errors
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "db"),
    "dbname": os.environ["POSTGRES_DB"],
    "user": os.environ["POSTGRES_USER"],
    "password": os.environ["POSTGRES_PASSWORD"],
    "connect_timeout": 2,
}


@contextmanager
def db():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn:
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()


def check_db():
    try:
        with db() as cur:
            cur.execute("SELECT 1")
        return True
    except psycopg2.Error:
        return False


@app.get("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not 3 <= len(username) <= 30 or len(password) < 6:
            flash("El usuario debe tener de 3 a 30 caracteres y la contraseña al menos 6.")
            return render_template("register.html")

        try:
            with db() as cur:
                cur.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                    (username, generate_password_hash(password)),
                )
        except psycopg2.errors.UniqueViolation:
            flash("Ese nombre de usuario ya existe.")
            return render_template("register.html")
        except psycopg2.Error:
            flash("La base de datos no está disponible.")
            return render_template("register.html")

        flash("Cuenta creada. Ya puedes iniciar sesión.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        try:
            with db() as cur:
                cur.execute(
                    "SELECT id, password_hash FROM users WHERE username = %s",
                    (username,),
                )
                row = cur.fetchone()
        except psycopg2.Error:
            flash("La base de datos no está disponible.")
            return render_template("login.html")

        if row is None or not check_password_hash(row[1], password):
            flash("Usuario o contraseña incorrectos.")
            return render_template("login.html")

        session.clear()
        session["user_id"] = row[0]
        session["username"] = username
        flash(f"Bienvenido, {username}.")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.post("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.")
    return redirect(url_for("index"))


@app.get("/status")
def status():
    db_ok = check_db()
    body = {"database": "up" if db_ok else "down"}
    return jsonify(body), (200 if db_ok else 503)