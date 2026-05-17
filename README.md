# 🛡️ HealthGuard AI — Health Insurance Price Prediction
### Full-Stack ML Web Application | Flask + MySQL + Scikit-Learn

---

## 📁 Project Structure

```
health_insurance_app/
├── app.py               ← Flask backend (all API routes)
├── model.pkl            ← Pre-trained ML model (GradientBoosting)
├── requirements.txt     ← Python dependencies
├── schema.sql           ← MySQL database schema
├── README.md            ← This file
└── templates/
    ├── index.html       ← Landing page
    ├── login.html       ← Login page
    ├── register.html    ← Registration page
    ├── predict.html     ← Prediction form + payment + history
    └── admin.html       ← Admin dashboard
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.9+
- MySQL 8.0+
- pip

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up MySQL Database
```bash
# Login to MySQL
mysql -u root -p

# Run the schema
mysql -u root -p < schema.sql
```

### 3.1 Start MySQL if it is not running
On Windows, start the MySQL service from Services or use:
```powershell
net start MySQL
```

On macOS / Linux systems, use the appropriate service manager, e.g.:
```bash
brew services start mysql
sudo systemctl start mysql
```

### 4. Configure Database Connection
Edit `app.py` — find `DB_CONFIG` near the top and update:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'YOUR_MYSQL_PASSWORD',   # ← Change this
    'database': 'health_insurance_db',
    'port': 3306
}
```
Or use environment variables:
```bash
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=health_insurance_db
```

### 4.1 SQLite Fallback
If MySQL is not available, the app can fall back to embedded SQLite automatically.
Use this environment variable to force SQLite instead of MySQL:
```bash
export DB_ENGINE=sqlite
```
You can also change the SQLite file path:
```bash
export SQLITE_DB_PATH=health_insurance.db
```

### 5. Run the Application
```bash
python app.py
```

### 6. Open in Browser
```
http://localhost:5010
```

---

## 🔑 Default Credentials

| Role  | Username | Password  |
|-------|----------|-----------|
| Admin | admin    | admin123  |

> **Note:** The default admin is auto-created by `app.py` on first run if it doesn't exist in the DB.

---

## 🌐 Application Pages

| URL           | Description                      |
|---------------|----------------------------------|
| `/`           | Landing / Home page              |
| `/login`      | User login                       |
| `/register`   | User registration                |
| `/predict`    | ML prediction form (auth required)|
| `/dashboard`  | Admin dashboard (admin only)     |

---

## 🔌 API Endpoints

### Authentication
| Method | Endpoint        | Description        |
|--------|-----------------|--------------------|
| POST   | `/api/register` | Register new user  |
| POST   | `/api/login`    | Login              |
| POST   | `/api/logout`   | Logout             |
| GET    | `/api/session`  | Check session      |

### Predictions (login required)
| Method | Endpoint        | Description              |
|--------|-----------------|--------------------------|
| POST   | `/api/predict`  | Get insurance prediction |
| GET    | `/api/history`  | User's prediction history|

### Payments (login required)
| Method | Endpoint        | Description         |
|--------|-----------------|---------------------|
| POST   | `/api/payment`  | Process payment     |

### Admin (admin role required)
| Method | Endpoint                  | Description            |
|--------|---------------------------|------------------------|
| GET    | `/api/admin/stats`        | Dashboard statistics   |
| GET    | `/api/admin/users`        | All users              |
| GET    | `/api/admin/predictions`  | All predictions        |
| GET    | `/api/admin/payments`     | All payments           |

---

## 🧠 ML Model

- **Algorithm:** Gradient Boosting Regressor (scikit-learn)
- **Features:** age, gender, BMI, children, smoker status, region
- **Training score:** ~99.8% (on training data)
- **Fallback:** If `model.pkl` is missing, an actuarial-style formula is used

### Prediction Input Schema
```json
{
  "age": 35,
  "gender": "male",
  "bmi": 24.5,
  "children": 2,
  "smoker": "no",
  "region": "northeast"
}
```

### Response
```json
{
  "predicted_price": 12450.35,
  "currency": "USD"
}
```

---

## 🔒 Security Features

- **Bcrypt** password hashing
- **Flask session** management with secret key
- **Role-based access control** (user / admin)
- **Input validation** on all endpoints
- **SQL injection protection** via parameterized queries

---

## 🛠️ Environment Variables (Optional)

| Variable    | Default              | Description          |
|-------------|----------------------|----------------------|
| SECRET_KEY  | `health_insurance_secret_2024` | Flask secret key |
| DB_HOST     | `localhost`          | MySQL host           |
| DB_USER     | `root`               | MySQL username       |
| DB_PASSWORD | `your_password`      | MySQL password       |
| DB_NAME     | `health_insurance_db`| Database name        |
| DB_PORT     | `3306`               | MySQL port           |

---

## 📦 Dependencies

```
flask          3.0.0   — Web framework
flask-cors     4.0.0   — CORS support
mysql-connector-python — MySQL driver
bcrypt         4.1.2   — Password hashing
numpy          1.26.2  — Numerical operations
scikit-learn   1.3.2   — ML model
```

---

## 🚀 Running on a Different Port

Change the last line of `app.py`:
```python
app.run(host='0.0.0.0', port=5010, debug=True)
```

---

*Built with Flask, MySQL, and Scikit-Learn.*
