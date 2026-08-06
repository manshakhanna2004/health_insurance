# 🛡️ HealthGuard AI – Health Insurance Price Prediction System

## 📌 Project Overview

HealthGuard AI is a Full Stack Machine Learning web application that predicts health insurance premiums based on user information. The system allows users to register, log in, estimate their insurance premium using a trained Machine Learning model, view prediction history, and simulate payments. An admin dashboard is also included to manage users, predictions, and payments.

This project demonstrates the integration of Machine Learning with a Flask web application and database management.

---

# 🎯 Project Objective

The objective of this project is to estimate health insurance premiums based on personal and medical details using Machine Learning. The application helps users understand the estimated insurance cost before purchasing an insurance policy.

---

# 🚀 Features

## User Features

- User Registration
- Secure Login & Logout
- Password Encryption using Bcrypt
- Health Insurance Premium Prediction
- Prediction History
- Payment Simulation
- User Profile

## Admin Features

- Admin Dashboard
- View All Users
- View All Predictions
- View Payment Records
- Dashboard Statistics

---

# 🛠️ Technologies Used

## Programming Language
- Python

## Backend
- Flask

## Frontend
- HTML
- CSS
- JavaScript

## Machine Learning
- Scikit-learn
- Gradient Boosting Regressor

## Database
- SQLite
- MySQL (Optional)

## Security
- Bcrypt Password Hashing
- Flask Session Authentication

## Model Storage
- Pickle (.pkl)

---

# 📂 Project Structure

```
HealthGuard-AI/
│
├── app.py
├── model.pkl
├── schema.sql
├── health_insurance.db
├── requirements.txt
├── README.md
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── predict.html
│   ├── profile.html
│   └── admin.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
└── database/
```

---

# 🤖 Machine Learning Model

### Algorithm Used

- Gradient Boosting Regressor

### Input Features

- Age
- Gender
- BMI
- Number of Children
- Smoking Status
- Region

### Output

- Estimated Health Insurance Premium

---

# 📊 Database Tables

## Users

Stores user information:

- User ID
- Username
- Email
- Password
- Role
- Created Date

---

## Predictions

Stores prediction history:

- Prediction ID
- User ID
- Age
- Gender
- BMI
- Children
- Smoker
- Region
- Predicted Premium
- Prediction Date

---

## Payments

Stores payment details:

- Payment ID
- User ID
- Amount
- Payment Method
- Transaction ID
- Payment Status
- Payment Date

---

# 🔐 Authentication

The application uses:

- Bcrypt for password hashing
- Flask Sessions for login management
- Role-based access (User/Admin)

---

# 🔄 Project Workflow

```
User

↓

Register / Login

↓

Enter Insurance Details

↓

Machine Learning Model

↓

Predict Insurance Premium

↓

Store Prediction

↓

Display Result

↓

Payment Simulation

↓

Prediction History
```

---

# 🌐 REST API Endpoints

## Authentication

```
POST /api/register
POST /api/login
POST /api/logout
GET  /api/session
```

## Prediction

```
POST /api/predict
GET  /api/history
```

## Payment

```
POST /api/payment
```

## Admin

```
GET /api/admin/users
GET /api/admin/predictions
GET /api/admin/payments
GET /api/admin/stats
```

---

# 📚 Topics Covered

### Python

- Functions
- Modules
- Exception Handling
- File Handling
- OOP Concepts
- Pickle

### Flask

- Routing
- Templates
- REST APIs
- Sessions
- Authentication
- JSON Responses

### Machine Learning

- Supervised Learning
- Regression
- Data Preprocessing
- Feature Engineering
- Model Training
- Model Evaluation
- Model Deployment

### Database

- SQLite
- MySQL
- CRUD Operations
- SQL Queries
- Foreign Keys

### Web Development

- HTML
- CSS
- JavaScript
- Responsive Design

### Security

- Password Hashing
- Authentication
- Authorization
- Session Management

### Software Engineering

- MVC Architecture
- Client-Server Architecture
- Database Design
- REST APIs

---

# ✅ Advantages

- User-friendly interface
- Secure authentication
- Fast premium prediction
- Prediction history
- Admin dashboard
- SQLite and MySQL support
- Easy deployment
- Machine Learning integration

---

# 🔮 Future Scope

- Online Payment Gateway
- Email Notifications
- PDF Report Generation
- JWT Authentication
- Insurance Recommendation System
- AI Chatbot Support
- Docker Deployment
- Cloud Deployment
- Mobile Application

---

# ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/HealthGuard-AI.git
```

### Navigate to Project

```bash
cd HealthGuard-AI
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
python app.py
```

### Open Browser

```
http://localhost:5010
```

---

# 📈 Applications

- Health Insurance Companies
- Insurance Premium Estimation
- Educational Machine Learning Projects
- Data Science Portfolio Projects
- College Major Projects

---

# 👩‍💻 Developer

**Mansha Khanna**

BCA (Data Science)

---

# 📄 License

This project is developed for educational and learning purposes.
