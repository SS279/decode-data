# 📖 Complete Setup Guide

This guide will walk you through setting up the Decode Data dbt Learning Platform from scratch.

## 📑 Table of Contents

1. [System Requirements](#system-requirements)
2. [Initial Setup](#initial-setup)
3. [MotherDuck Configuration](#motherduck-configuration)
4. [Database Setup](#database-setup)
5. [dbt Project Setup](#dbt-project-setup)
6. [Running the Application](#running-the-application)
7. [Creating Lessons](#creating-lessons)
8. [Troubleshooting](#troubleshooting)

## 🖥️ System Requirements

### Required Software

- **Python**: 3.9 or higher
- **pip**: Latest version
- **Git**: For version control
- **dbt-duckdb**: Will be installed via requirements

### Recommended

- **VS Code** or **PyCharm**: For code editing
- **DBeaver** or **DataGrip**: For database management (optional)

### Operating System

- macOS, Linux, or Windows with WSL2

## 🔧 Initial Setup

### 1. Get the Code

```bash
# If cloning from git
git clone <your-repository-url>
cd decode_data_project

# Or if starting fresh
mkdir decode_data_project
cd decode_data_project
# Copy all project files here
```

### 2. Create Virtual Environment

**Why?** Isolates project dependencies from your system Python.

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed Django-4.2.7 duckdb-0.9.2 dbt-duckdb-1.6.2 ...
```

### 4. Verify Installation

```bash
# Check Django
python -c "import django; print(django.get_version())"
# Should print: 4.2.7

# Check dbt
dbt --version
# Should show dbt version information

# Check duckdb
python -c "import duckdb; print(duckdb.__version__)"
# Should print: 0.9.2
```

## ☁️ MotherDuck Configuration

### 1. Create MotherDuck Account

1. Go to [motherduck.com](https://motherduck.com)
2. Sign up for a free account
3. Verify your email

### 2. Get Your Token

1. Log in to MotherDuck
2. Go to Settings → API Tokens
3. Click "Create New Token"
4. Copy the token (starts with `eyJ...`)

### 3. Create Database/Share

In MotherDuck:

```sql
-- Create a database for the project
CREATE DATABASE decode_dbt;

-- Verify it's created
SHOW DATABASES;
```

## ⚙️ Environment Configuration

### 1. Create .env File

```bash
cp .env.example .env
```

### 2. Generate Secret Key

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and paste it into your `.env` file.

### 3. Complete .env Configuration

Edit `.env`:

```env
# Django Settings
SECRET_KEY=<paste-your-generated-key-here>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database - leave empty for SQLite (recommended for local dev)
DATABASE_URL=

# MotherDuck Configuration
MOTHERDUCK_TOKEN=<paste-your-token-here>
MOTHERDUCK_SHARE=decode_dbt
```

**Important Security Notes:**
- Never commit `.env` to Git
- Use strong, unique SECRET_KEY in production
- Rotate tokens regularly

## 🗄️ Database Setup

### 1. Create Database Schema

```bash
# Create migration files
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

**Expected output:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, learning, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying learning.0001_initial... OK
  ...
```

### 2. Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

Follow the prompts:
```
Username: admin
Email: admin@example.com
Password: ********
Password (again): ********
Superuser created successfully.
```

### 3. Verify Database

```bash
# Check that tables were created
python manage.py showmigrations
```

## 📦 dbt Project Setup

### 1. Understand dbt Project Structure

```
dbt_project/
├── dbt_project.yml          # Main configuration
├── models/                  # SQL transformation models
│   ├── hello_dbt/
│   │   ├── customers.sql
│   │   └── orders.sql
│   ├── cafe_chain/
│   └── energy_smart/
└── seeds/                   # CSV seed data
    ├── hello_dbt/
    │   ├── raw_customers.csv
    │   └── raw_orders.csv
    ├── cafe_chain/
    └── energy_smart/
```

### 2. Create Your First Lesson

The project comes with a sample "Hello dbt" lesson. To add your own:

1. **Create model directory:**
   ```bash
   mkdir -p dbt_project/models/my_lesson
   ```

2. **Add SQL models:**
   ```bash
   touch dbt_project/models/my_lesson/my_model.sql
   ```

3. **Create seed data:**
   ```bash
   mkdir -p dbt_project/seeds/my_lesson
   touch dbt_project/seeds/my_lesson/raw_data.csv
   ```

4. **Update lesson configuration** in `learning/views.py`:
   ```python
   LESSONS = [
       {
           "id": "my_lesson",
           "title": "My Custom Lesson",
           "description": "Learn something amazing!",
           "model_dir": "models/my_lesson",
           "validation": {
               "sql": "SELECT COUNT(*) AS models_built FROM information_schema.tables WHERE table_schema=current_schema()",
               "expected_min": 1
           },
       },
       # ... other lessons
   ]
   ```

## 🚀 Running the Application

### 1. Start Development Server

```bash
python manage.py runserver
```

**Expected output:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

### 2. Access the Application

Open your browser and navigate to:

- **Homepage:** http://localhost:8000
- **Admin:** http://localhost:8000/admin

### 3. Test the Application

1. Register a new user account
2. Login with your credentials
3. View the dashboard
4. Select a lesson
5. Initialize workspace
6. Load seeds
7. Execute a model

## 📊 Creating Complete Lessons

### Lesson Components

A complete lesson needs:

1. **SQL Models** (in `dbt_project/models/lesson_id/`)
2. **Seed Data** (in `dbt_project/seeds/lesson_id/`)
3. **Lesson Configuration** (in `learning/views.py`)

### Example: Creating "Café Chain" Lesson

#### 1. Create Models

`dbt_project/models/cafe_chain/sales_summary.sql`:
```sql
{{ config(materialized='table') }}

SELECT
    store_id,
    DATE_TRUNC('month', sale_date) AS sale_month,
    SUM(amount) AS total_sales,
    COUNT(*) AS transaction_count,
    AVG(amount) AS avg_transaction
FROM {{ ref('raw_sales') }}
GROUP BY store_id, sale_month
```

#### 2. Create Seed Data

`dbt_project/seeds/cafe_chain/raw_sales.csv`:
```csv
sale_id,store_id,sale_date,amount
1,101,2024-01-15,45.50
2,101,2024-01-16,32.00
3,102,2024-01-15,28.75
...
```

#### 3. Add Lesson Configuration

In `learning/views.py`:
```python
{
    "id": "cafe_chain",
    "title": "☕ Café Chain Analytics",
    "description": "Analyze coffee shop sales data",
    "model_dir": "models/cafe_chain",
    "validation": {
        "sql": "SELECT COUNT(*) AS models_built FROM information_schema.tables WHERE table_schema=current_schema()",
        "expected_min": 2
    },
}
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Issue: "dbt command not found"

**Solution:**
```bash
pip install dbt-duckdb
which dbt  # Verify installation
```

#### Issue: "MotherDuck connection failed"

**Solution:**
1. Check token in `.env` file
2. Test connection:
   ```python
   python manage.py shell
   >>> from learning.storage import MotherDuckStorage
   >>> storage = MotherDuckStorage()
   >>> conn = storage._get_connection()
   >>> print("Connected!")
   ```

#### Issue: "Workspace initialization fails"

**Solution:**
1. Check `dbt_project` directory exists
2. Verify `dbt_project.yml` is valid
3. Check model directories match lesson config
4. Review logs in `debug.log`

#### Issue: "Static files not loading"

**Solution:**
```bash
python manage.py collectstatic --noinput
```

#### Issue: "Migration errors"

**Solution:**
```bash
# Reset database (development only!)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Getting Help

1. Check application logs: `debug.log`
2. Check Django debug page (if DEBUG=True)
3. Review MotherDuck logs in their dashboard
4. Test dbt separately:
   ```bash
   cd /tmp/test_dbt_workspace
   dbt debug
   ```

## 📝 Next Steps

After setup is complete:

1. ✅ Review the [README.md](README.md) for detailed documentation
2. ✅ Read the [QUICKSTART.md](QUICKSTART.md) for quick reference
3. ✅ Explore the application as a learner
4. ✅ Create custom lessons for your needs
5. ✅ Configure for production deployment (see deployment guide)

## 🎉 Success Checklist

Before considering setup complete:

- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] `.env` file configured with valid credentials
- [ ] Database migrated successfully
- [ ] Superuser created
- [ ] dbt project structure in place
- [ ] Application starts without errors
- [ ] Can register and login
- [ ] Can initialize workspace
- [ ] Can execute dbt models
- [ ] Can run SQL queries

---

**Need more help?** Create an issue in the repository or contact support.