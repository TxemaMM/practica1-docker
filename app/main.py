import os

import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "db"),
    "dbname": os.environ["POSTGRES_DB"],
    "user": os.environ["POSTGRES_USER"],
    "password": os.environ["POSTGRES_PASSWORD"],
}


def check_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG, connect_timeout=2)
        conn.close()
        return True
    except psycopg2.Error:
        return False


@app.get("/")
def index():
    return "Hola desde Flask"


@app.get("/status")
def status():
    db_ok = check_db()
    body = {"database": "up" if db_ok else "down"}
    return jsonify(body), (200 if db_ok else 503)