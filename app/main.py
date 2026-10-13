import os
from contextlib import contextmanager
from functools import wraps

import json
import redis
import time
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

CACHE_ENABLED = os.environ.get("CACHE_ENABLED", "false").lower() == "true"
CACHE_TTL = int(os.environ.get("CACHE_TTL", "30"))
TOP_KEY = "ranking:top5"

cache = None
if CACHE_ENABLED:
    cache = redis.Redis(
        host=os.environ.get("REDIS_HOST", "cache"),
        port=6379,
        password=os.environ.get("REDIS_PASSWORD") or None,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
    )

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

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Inicia sesión para hacer eso.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def top5_from_db():
    with db() as cur:
        cur.execute("""
            SELECT g.name, COUNT(v.id) AS votes
            FROM games g
            LEFT JOIN votes v ON v.game_id = g.id
            GROUP BY g.id, g.name
            ORDER BY votes DESC, g.name
            LIMIT 5
        """)
        return [{"name": r[0], "votes": r[1]} for r in cur.fetchall()]


def get_top5():
    """Devuelve (filas, origen, milisegundos). Origen: 'cache' o 'db'."""
    start = time.perf_counter()
    rows, source = None, "db"

    if cache is not None:
        try:
            raw = cache.get(TOP_KEY)
            if raw is not None:
                rows, source = json.loads(raw), "cache"
        except redis.RedisError:
            pass

    if rows is None:
        rows = top5_from_db()
        if cache is not None:
            try:
                cache.setex(TOP_KEY, CACHE_TTL, json.dumps(rows))
            except redis.RedisError:
                pass

    elapsed = round((time.perf_counter() - start) * 1000, 1)
    return rows, source, elapsed


def invalidate_cache():
    if cache is not None:
        try:
            cache.delete(TOP_KEY)
        except redis.RedisError:
            pass


def cache_state():
    if cache is None:
        return "disabled"
    try:
        cache.ping()
        return "up"
    except redis.RedisError:
        return "down"

@app.get("/")
def index():
    games, voted, db_error = [], set(), False
    top, source, elapsed = [], None, None       
    try:
        top, source, elapsed = get_top5()     
        with db() as cur:
            cur.execute("""
                SELECT g.id, g.name, COUNT(v.id) AS votes
                FROM games g
                LEFT JOIN votes v ON v.game_id = g.id
                GROUP BY g.id, g.name
                ORDER BY votes DESC, g.name
            """)
            games = cur.fetchall()
            if "user_id" in session:
                cur.execute(
                    "SELECT game_id FROM votes WHERE user_id = %s",
                    (session["user_id"],),
                )
                voted = {r[0] for r in cur.fetchall()}
    except psycopg2.Error:
        db_error = True
    return render_template("index.html", games=games, voted=voted, db_error=db_error,
                           top=top, source=source, elapsed=elapsed)


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


@app.post("/games")
@login_required
def add_game():
    name = request.form.get("name", "").strip()
    if not 1 <= len(name) <= 60:
        flash("El nombre debe tener entre 1 y 60 caracteres.")
        return redirect(url_for("index"))
    try:
        with db() as cur:
            cur.execute(
                "INSERT INTO games (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                (name,),
            )
            added = cur.rowcount == 1
    except psycopg2.Error:
        flash("La base de datos no está disponible.")
        return redirect(url_for("index"))
    if added:
        invalidate_cache()
    flash("Videojuego añadido." if added else "Ese videojuego ya estaba en la lista.")
    return redirect(url_for("index"))


@app.post("/games/<int:game_id>/vote")
@login_required
def vote(game_id):
    try:
        with db() as cur:
            cur.execute(
                "INSERT INTO votes (user_id, game_id) VALUES (%s, %s) "
                "ON CONFLICT (user_id, game_id) DO NOTHING",
                (session["user_id"], game_id),
            )
            counted = cur.rowcount == 1
    except psycopg2.errors.ForeignKeyViolation:
        flash("Ese videojuego no existe.")
        return redirect(url_for("index"))
    except psycopg2.Error:
        flash("La base de datos no está disponible.")
        return redirect(url_for("index"))
    if counted:
        invalidate_cache()
    flash("Voto registrado." if counted else "Ya habías votado ese videojuego.")
    return redirect(url_for("index"))


@app.get("/status")
def status():
    db_ok = check_db()
    cache_s = cache_state()

    if not db_ok:
        overall, code = "down", 503
    elif cache_s == "down":
        overall, code = "degraded", 200
    else:
        overall, code = "ok", 200

    return jsonify(status=overall, database="up" if db_ok else "down", cache=cache_s), code