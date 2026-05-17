"""
Health Insurance Price Prediction - Flask Backend
Main application entry point — PostgreSQL edition
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from flask_cors import CORS
import psycopg2
import psycopg2.extras          # RealDictCursor
from psycopg2 import OperationalError
import bcrypt
import pickle
import numpy as np
import os
import json
from datetime import datetime
from functools import wraps
import logging
import csv
import io
import random
import string

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'health_insurance_secret_2024')
CORS(app)

# ─── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Database Configuration ────────────────────────────────────────────────────
DB_CONFIG = {
    'host':     os.environ.get('DB_HOST',     'localhost'),
    'user':     os.environ.get('DB_USER',     'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'mansha123'),  
    'dbname':   os.environ.get('DB_NAME',     'health_insurance_db'),
    'port':     int(os.environ.get('DB_PORT', 5432)),
    'connect_timeout': int(os.environ.get('DB_TIMEOUT', 5)),
}

DB_ERROR_MESSAGE = (
    'Database unavailable. '
    'Start PostgreSQL and verify DB_HOST/DB_USER/DB_PASSWORD/DB_NAME.'
)

# ─── Database Helper ───────────────────────────────────────────────────────────

def get_db():
    """Return a new psycopg2 connection, or None on failure."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except OperationalError as e:
        logger.error(f"PostgreSQL connection error: {e}")
        return None


def get_cursor(conn, dictionary=False):
    """Return a cursor.  dictionary=True gives RealDictCursor (dict-like rows)."""
    if dictionary:
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return conn.cursor()


def serialize_rows(rows):
    """Convert psycopg2 RealDictRow objects to plain dicts for JSON."""
    return [dict(row) for row in rows]


def build_csv_response(rows, filename):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Username', 'Age', 'Gender', 'BMI',
        'Children', 'Smoker', 'Region', 'Predicted Price', 'Created At'
    ])
    for row in rows:
        writer.writerow([
            row['id'], row['username'], row['age'], row['gender'], row['bmi'],
            row['children'], row['smoker'], row['region'],
            row['predicted_price'], row['created_at']
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


def fetch_prediction_rows(smoker=None):
    conn = get_db()
    if not conn:
        return None
    cursor = get_cursor(conn, dictionary=True)
    query = """
        SELECT p.id, u.username, p.age, p.gender, p.bmi, p.children,
               p.smoker, p.region, p.predicted_price, p.created_at
        FROM predictions p
        JOIN users u ON u.id = p.user_id
    """
    params = ()
    if smoker is not None:
        query += " WHERE LOWER(p.smoker) = %s"
        params = (smoker,)
    query += " ORDER BY p.created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows


def create_database_if_missing():
    """
    PostgreSQL does not support CREATE DATABASE inside a transaction.
    Connect to the default 'postgres' database and create ours if absent.
    """
    admin_cfg = {**DB_CONFIG, 'dbname': 'postgres'}
    try:
        conn = psycopg2.connect(**admin_cfg)
        conn.autocommit = True          # required for CREATE DATABASE
        cursor = conn.cursor()
        target = DB_CONFIG['dbname']
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target,))
        if not cursor.fetchone():
            cursor.execute(f'CREATE DATABASE "{target}"')
            logger.info(f"Database '{target}' created.")
        cursor.close(); conn.close()
    except Exception as e:
        logger.error(f"Cannot create database: {e}")


def init_db():
    """Initialize the database schema."""
    try:
        create_database_if_missing()

        conn = get_db()
        if not conn:
            logger.warning('Could not connect to PostgreSQL. Running without database.')
            return

        cursor = conn.cursor()

        # ── Users ────────────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            SERIAL PRIMARY KEY,
                username      VARCHAR(50)  UNIQUE NOT NULL,
                email         VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name     VARCHAR(100),
                role          VARCHAR(10)  NOT NULL DEFAULT 'user'
                                  CHECK (role IN ('user','admin')),
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Predictions ───────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id              SERIAL PRIMARY KEY,
                user_id         INTEGER NOT NULL
                                    REFERENCES users(id) ON DELETE CASCADE,
                age             INTEGER,
                gender          VARCHAR(10),
                bmi             FLOAT,
                children        INTEGER,
                smoker          VARCHAR(5),
                region          VARCHAR(20),
                predicted_price FLOAT,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Payments ──────────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id             SERIAL PRIMARY KEY,
                user_id        INTEGER NOT NULL
                                   REFERENCES users(id) ON DELETE CASCADE,
                amount         FLOAT NOT NULL,
                payment_method VARCHAR(50),
                status         VARCHAR(10) NOT NULL DEFAULT 'pending'
                                   CHECK (status IN ('pending','completed','failed')),
                transaction_id VARCHAR(100),
                plan_type      VARCHAR(50),
                created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

        # ── Default admin ─────────────────────────────────────────────────────
        cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
        if not cursor.fetchone():
            hashed = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s, %s)
            """, ('admin', 'admin@healthinsure.com', hashed, 'System Admin', 'admin'))
            conn.commit()
            logger.info('Default admin created: admin / admin123')

        cursor.close(); conn.close()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


# ─── ML Model Loading ──────────────────────────────────────────────────────────
MODEL = None
try:
    with open('model.pkl', 'rb') as f:
        MODEL = pickle.load(f)
    logger.info("ML model loaded successfully.")
except FileNotFoundError:
    logger.warning("model.pkl not found. Using fallback prediction formula.")

# ─── Auth Decorators ───────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

# ─── Prediction Logic ──────────────────────────────────────────────────────────
def predict_insurance(age, gender, bmi, children, smoker, region):
    if MODEL:
        gender_enc = 1 if gender == 'male' else 0
        smoker_enc = 1 if smoker == 'yes' else 0
        region_map = {'northeast': 0, 'northwest': 1, 'southeast': 2, 'southwest': 3}
        region_enc = region_map.get(region, 0)
        features = np.array([[age, gender_enc, bmi, children, smoker_enc, region_enc]])
        price = MODEL.predict(features)[0]
    else:
        base = 3000
        price = base + age * 250 + bmi * 120 + children * 400
        if smoker == 'yes':
            price *= 2.8
        if gender == 'male':
            price += 300
        region_adj = {'northeast': 1.1, 'northwest': 1.05, 'southeast': 1.0, 'southwest': 0.95}
        price *= region_adj.get(region, 1.0)
    return round(float(price), 2)

# ─── Routes: Pages ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html', username=session.get('username'), logged_in='user_id' in session)

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect('/')
    return render_template('login.html')

@app.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect('/')
    return render_template('register.html')

@app.route('/predict')
def predict_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('predict.html', username=session.get('username'))

@app.route('/dashboard')
def dashboard_page():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')
    return render_template('admin.html', username=session.get('username'))

@app.route('/profile')
def profile_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('profile.html', username=session.get('username'))

# ─── API: Authentication ───────────────────────────────────────────────────────
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username  = data.get('username', '').strip()
    email     = data.get('email', '').strip()
    password  = data.get('password', '')
    full_name = data.get('full_name', '').strip()

    if not all([username, email, password, full_name]):
        return jsonify({'error': 'All fields are required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    conn = get_db()
    if not conn:
        return jsonify({'error': DB_ERROR_MESSAGE}), 503
    cursor = get_cursor(conn, dictionary=True)
    cursor.execute(
        "SELECT id FROM users WHERE username = %s OR email = %s",
        (username, email)
    )
    if cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'error': 'Username or email already exists'}), 409

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name)
        VALUES (%s, %s, %s, %s)
    """, (username, email, hashed, full_name))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'message': 'Registration successful'}), 201


@app.route('/api/login', methods=['POST'])
def login():
    data     = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    conn = get_db()
    if not conn:
        return jsonify({'error': DB_ERROR_MESSAGE}), 503
    cursor = get_cursor(conn, dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE username = %s OR email = %s",
        (username, username)
    )
    user = cursor.fetchone()
    cursor.close(); conn.close()

    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return jsonify({'error': 'Invalid credentials'}), 401

    session['user_id']  = user['id']
    session['username'] = user['username']
    session['role']     = user['role']
    session.permanent   = True
    redirect_url = '/dashboard' if user['role'] == 'admin' else '/'
    return jsonify({'message': 'Login successful', 'role': user['role'], 'redirect': redirect_url})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})


@app.route('/api/session')
def check_session():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'username': session['username'], 'role': session['role']})
    return jsonify({'logged_in': False})


@app.route('/api/profile')
@login_required
def get_profile():
    conn = get_db()
    if not conn:
        return jsonify({'error': DB_ERROR_MESSAGE}), 503
    cursor = get_cursor(conn, dictionary=True)

    cursor.execute(
        "SELECT id, username, email, full_name, created_at FROM users WHERE id = %s",
        (session['user_id'],)
    )
    user = cursor.fetchone()
    if not user:
        cursor.close(); conn.close()
        return jsonify({'error': 'User not found'}), 404

    cursor.execute("""
        SELECT COUNT(*) AS count, AVG(predicted_price) AS avg_price
        FROM predictions WHERE user_id = %s
    """, (session['user_id'],))
    stats = cursor.fetchone()
    cursor.close(); conn.close()

    return jsonify({
        'username':         user['username'],
        'email':            user['email'],
        'full_name':        user['full_name'],
        'created_at':       str(user['created_at']),
        'prediction_count': stats['count'] or 0,
        'avg_price':        float(stats['avg_price'] or 0),
    })


@app.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    data      = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    email     = data.get('email', '').strip()

    if not full_name or not email:
        return jsonify({'error': 'Full name and email are required.'}), 400

    conn = get_db()
    if not conn:
        return jsonify({'error': DB_ERROR_MESSAGE}), 503

    cursor = get_cursor(conn, dictionary=True)
    cursor.execute(
        "SELECT id FROM users WHERE email = %s AND id <> %s",
        (email, session['user_id'])
    )
    if cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'error': 'Email is already in use.'}), 409

    cursor.execute(
        "UPDATE users SET full_name = %s, email = %s WHERE id = %s",
        (full_name, email, session['user_id'])
    )
    conn.commit()

    cursor.execute(
        "SELECT id, username, email, full_name, created_at FROM users WHERE id = %s",
        (session['user_id'],)
    )
    user = cursor.fetchone()
    cursor.close(); conn.close()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'username':   user['username'],
        'email':      user['email'],
        'full_name':  user['full_name'],
        'created_at': str(user['created_at']),
    })

# ─── API: Prediction ───────────────────────────────────────────────────────────
@app.route('/api/predict', methods=['POST'])
@login_required
def predict():
    data = request.get_json()
    try:
        age      = int(data['age'])
        bmi      = float(data['bmi'])
        children = int(data['children'])
        gender   = data['gender'].lower()
        smoker   = data['smoker'].lower()
        region   = data['region'].lower()
    except (KeyError, ValueError) as e:
        return jsonify({'error': f'Invalid input: {e}'}), 400

    if not (1 <= age <= 120):
        return jsonify({'error': 'Age must be between 1 and 120'}), 400
    if not (10.0 <= bmi <= 60.0):
        return jsonify({'error': 'BMI must be between 10 and 60'}), 400
    if not (0 <= children <= 10):
        return jsonify({'error': 'Children must be between 0 and 10'}), 400

    price = predict_insurance(age, gender, bmi, children, smoker, region)

    conn = get_db()
    if conn:
        cursor = get_cursor(conn)
        cursor.execute("""
            INSERT INTO predictions
                (user_id, age, gender, bmi, children, smoker, region, predicted_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (session['user_id'], age, gender, bmi, children, smoker, region, price))
        conn.commit()
        cursor.close(); conn.close()

    return jsonify({'predicted_price': price, 'currency': 'INR'})


@app.route('/api/history')
@login_required
def get_history():
    conn = get_db()
    if not conn:
        return jsonify([])
    cursor = get_cursor(conn, dictionary=True)
    cursor.execute("""
        SELECT id, age, gender, bmi, children, smoker, region, predicted_price,
               TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') AS date
        FROM predictions
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 20
    """, (session['user_id'],))
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(serialize_rows(rows))

# ─── API: Payment ──────────────────────────────────────────────────────────────
@app.route('/api/payment', methods=['POST'])
@login_required
def process_payment():
    data   = request.get_json()
    amount = data.get('amount', 0)
    method = data.get('payment_method', 'card')
    plan   = data.get('plan_type', 'basic')
    txn_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    status = 'completed'

    conn = get_db()
    if conn:
        cursor = get_cursor(conn)
        cursor.execute("""
            INSERT INTO payments
                (user_id, amount, payment_method, status, transaction_id, plan_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session['user_id'], amount, method, status, txn_id, plan))
        conn.commit()
        cursor.close(); conn.close()

    return jsonify({'status': status, 'transaction_id': txn_id, 'amount': amount})

# ─── API: Admin ────────────────────────────────────────────────────────────────
@app.route('/api/admin/users')
@admin_required
def admin_users():
    conn = get_db()
    if not conn:
        return jsonify([])
    cursor = get_cursor(conn, dictionary=True)
    cursor.execute("""
        SELECT u.id, u.username, u.email, u.full_name, u.role,
               TO_CHAR(u.created_at, 'YYYY-MM-DD') AS joined,
               COUNT(DISTINCT p.id)   AS predictions,
               COUNT(DISTINCT pay.id) AS payments
        FROM users u
        LEFT JOIN predictions p   ON p.user_id   = u.id
        LEFT JOIN payments    pay ON pay.user_id  = u.id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """)
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(serialize_rows(rows))


@app.route('/api/admin/predictions')
@admin_required
def admin_predictions():
    conn = get_db()
    if not conn:
        return jsonify([])
    cursor = get_cursor(conn, dictionary=True)
    cursor.execute("""
        SELECT p.*, u.username,
               TO_CHAR(p.created_at, 'YYYY-MM-DD HH24:MI') AS date
        FROM predictions p
        JOIN users u ON u.id = p.user_id
        ORDER BY p.created_at DESC
        LIMIT 100
    """)
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(serialize_rows(rows))


@app.route('/api/admin/payments')
@admin_required
def admin_payments():
    conn = get_db()
    if not conn:
        return jsonify([])
    cursor = get_cursor(conn, dictionary=True)
    cursor.execute("""
        SELECT pay.*, u.username,
               TO_CHAR(pay.created_at, 'YYYY-MM-DD HH24:MI') AS date
        FROM payments pay
        JOIN users u ON u.id = pay.user_id
        ORDER BY pay.created_at DESC
        LIMIT 100
    """)
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(serialize_rows(rows))


@app.route('/api/admin/stats')
@admin_required
def admin_stats():
    conn = get_db()
    if not conn:
        return jsonify({})
    cursor = get_cursor(conn, dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total FROM users")
    users = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) AS total FROM predictions")
    preds = cursor.fetchone()['total']
    cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM payments WHERE status = 'completed'")
    revenue = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) AS total FROM payments WHERE status = 'completed'")
    paid = cursor.fetchone()['total']
    cursor.close(); conn.close()
    return jsonify({'users': users, 'predictions': preds, 'revenue': float(revenue), 'payments': paid})


@app.route('/api/admin/analytics')
@admin_required
def admin_analytics():
    conn = get_db()
    if not conn:
        return jsonify({})
    cursor = get_cursor(conn, dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    users_row = cursor.fetchone() or {'total_users': 0}

    cursor.execute("""
        SELECT COUNT(*) AS total_predictions, AVG(predicted_price) AS avg_price
        FROM predictions
    """)
    pred_row = cursor.fetchone() or {'total_predictions': 0, 'avg_price': 0}
    avg_price        = float(pred_row['avg_price'] or 0)
    total_predictions = int(pred_row['total_predictions'] or 0)

    cursor.execute("SELECT smoker, COUNT(*) AS count FROM predictions GROUP BY smoker")
    smoker_rows = cursor.fetchall()
    smoker_counts = {'yes': 0, 'no': 0}
    for r in smoker_rows:
        key = (r.get('smoker') or 'no').lower()
        smoker_counts[key] = int(r.get('count', 0))

    # PostgreSQL date truncation
    cursor.execute("""
        SELECT TO_CHAR(created_at, 'YYYY-MM') AS month, COUNT(*) AS count
        FROM predictions
        GROUP BY TO_CHAR(created_at, 'YYYY-MM')
        ORDER BY month ASC
    """)
    monthly_rows   = cursor.fetchall()
    monthly_counts = serialize_rows(monthly_rows)

    cursor.close(); conn.close()
    return jsonify({
        'total_users':       int(users_row.get('total_users', 0)),
        'total_predictions': total_predictions,
        'avg_price':         avg_price,
        'smoker_counts':     smoker_counts,
        'monthly_counts':    monthly_counts,
    })

# ─── API: Download ────────────────────────────────────────────────────────────
@app.route('/api/download/all-data')
@app.route('/api/download/all_data')
@app.route('/api/download/all')
@login_required
def download_all_data():
    rows = fetch_prediction_rows()
    if rows is None:
        return jsonify({'error': DB_ERROR_MESSAGE}), 503
    return build_csv_response(rows, 'all_prediction_data.csv')

@app.route('/api/download/smoker-data')
@app.route('/api/download/smoker_data')
@app.route('/api/download/smokers')
@login_required
def download_smoker_data():
    rows = fetch_prediction_rows(smoker='yes')
    if rows is None:
        return jsonify({'error': DB_ERROR_MESSAGE}), 503
    return build_csv_response(rows, 'smoker_data.csv')

@app.route('/api/download/non-smoker-data')
@app.route('/api/download/non_smoker_data')
@app.route('/api/download/non-smokers')
@login_required
def download_non_smoker_data():
    rows = fetch_prediction_rows(smoker='no')
    if rows is None:
        return jsonify({'error': DB_ERROR_MESSAGE}), 503
    return build_csv_response(rows, 'non_smoker_data.csv')

# ─── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5010, debug=True, use_reloader=False)
