# 🎓 Decode Data - dbt Learning Platform

A Django-based interactive learning platform for teaching dbt (data build tool) concepts through hands-on exercises with MotherDuck integration.

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running Locally](#running-locally)
- [Project Structure](#project-structure)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)

## ✨ Features

- **User Authentication**: Register, login, and personalized learning experience
- **Interactive Lessons**: Three hands-on dbt lessons (Hello dbt, Café Chain Analytics, Energy Smart)
- **Model Builder**: Edit and execute dbt models directly in the browser
- **Query Visualizer**: Run SQL queries against your MotherDuck schema
- **Progress Tracking**: Monitor your learning progress and achievements
- **Isolated Workspaces**: Each user gets their own dbt workspace and MotherDuck schema

## 🔧 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+**: [Download Python](https://www.python.org/downloads/)
- **pip**: Python package installer (comes with Python)
- **dbt-core**: Will be installed via requirements.txt
- **MotherDuck Account**: [Sign up for MotherDuck](https://motherduck.com/)
- **Git**: For version control

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd decode_data_project
```

### 2. Create a Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### 1. Create Environment File

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

### 2. Edit `.env` File

Open `.env` and configure the following:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-generate-a-new-one
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Leave empty for SQLite in development)
DATABASE_URL=

# MotherDuck Configuration
MOTHERDUCK_TOKEN=your-motherduck-token-here
MOTHERDUCK_SHARE=decode_dbt
```

**Important:**
- **SECRET_KEY**: Generate a new secret key using Python:
  ```python
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- **MOTHERDUCK_TOKEN**: Get your token from [MotherDuck Settings](https://motherduck.com/settings)
- **MOTHERDUCK_SHARE**: Name of your MotherDuck database/share (default: `decode_dbt`)

### 3. Set Up dbt Project

Create a `dbt_project` directory in the project root with the following structure:

```
dbt_project/
├── dbt_project.yml
├── models/
│   ├── hello_dbt/
│   │   ├── model1.sql
│   │   └── model2.sql
│   ├── cafe_chain/
│   │   └── ...
│   └── energy_smart/
│       └── ...
└── seeds/
    ├── hello_dbt/
    ├── cafe_chain/
    └── energy_smart/
```

**Example `dbt_project.yml`:**
```yaml
name: 'decode_dbt'
version: '1.0.0'
config-version: 2

profile: 'decode_dbt'

model-paths: ["models"]
seed-paths: ["seeds"]
target-path: "target"

models:
  decode_dbt:
    +materialized: table
```

## 🏃 Running Locally

### 1. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Create a Superuser (Optional - for admin access)

```bash
python manage.py createsuperuser
```

### 3. Collect Static Files (if needed)

```bash
python manage.py collectstatic --noinput
```

### 4. Run the Development Server

```bash
python manage.py runserver
```

### 5. Access the Application

Open your browser and navigate to:
- **Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin (if you created a superuser)

## 📁 Project Structure

```
decode_data_project/
│
├── manage.py                     # Django command-line tool
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (not in git)
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
│
├── decode_data/                  # Main Django project
│   ├── __init__.py
│   ├── settings.py               # ⭐ Django settings
│   ├── urls.py                   # Main URL routing
│   ├── wsgi.py                   # WSGI interface
│   └── asgi.py                   # ASGI interface
│
├── learning/                     # Main application
│   ├── __init__.py
│   ├── models.py                 # ⭐ Database models
│   ├── views.py                  # ⭐ View controllers
│   ├── forms.py                  # Web forms
│   ├── urls.py                   # App URL routing
│   ├── admin.py                  # Admin interface config
│   ├── apps.py                   # App configuration
│   ├── dbt_manager.py            # ⭐ dbt operations manager
│   ├── storage.py                # ⭐ MotherDuck interface
│   │
│   ├── templates/                # HTML templates
│   │   ├── base.html
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   └── learning/
│   │       ├── dashboard.html
│   │       ├── lesson_detail.html
│   │       ├── model_builder.html
│   │       ├── query_visualize.html
│   │       └── progress.html
│   │
│   ├── static/                   # Static files
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   └── migrations/               # Database migrations
│
└── dbt_project/                  # Your dbt project
    ├── dbt_project.yml
    ├── models/
    └── seeds/
```

## 📖 Usage Guide

### For Learners

1. **Register an Account**
   - Navigate to the registration page
   - Create your account with username, email, and password

2. **Choose a Lesson**
   - After login, you'll see the dashboard with available lessons
   - Click on a lesson to start learning

3. **Model Builder**
   - Initialize your workspace (first-time setup)
   - Load seed data
   - Edit SQL models
   - Execute models and see results

4. **Query & Visualize**
   - Write SQL queries against your schema
   - View results in a formatted table
   - Explore your transformed data

5. **Track Progress**
   - Monitor your learning progress
   - See completed steps and achievements

### For Administrators

Access the Django admin panel at `/admin` to:
- Manage users
- View learner progress
- Monitor model edits
- Check user sessions

## 🔍 Troubleshooting

### Common Issues

**1. dbt command not found**
```bash
# Ensure dbt is installed
pip install dbt-duckdb
dbt --version
```

**2. MotherDuck connection failed**
- Verify your `MOTHERDUCK_TOKEN` in `.env`
- Check that the token has proper permissions
- Ensure `MOTHERDUCK_SHARE` exists in your MotherDuck account

**3. Database errors**
```bash
# Reset migrations if needed
python manage.py migrate --run-syncdb
```

**4. Static files not loading**
```bash
# Collect static files
python manage.py collectstatic --noinput
```

**5. Workspace initialization fails**
- Ensure the `dbt_project` directory exists
- Check that model directories match lesson configuration in `views.py`
- Verify dbt project structure

### Debug Mode

To see detailed error messages, ensure `DEBUG=True` in your `.env` file (development only).

### Logs

Check Django logs in `debug.log` for detailed error information.

## 🛠️ Development

### Database Migrations

After modifying models:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Creating New Lessons

1. Add lesson configuration in `learning/views.py` in the `LESSONS` list
2. Create corresponding model directory in `dbt_project/models/`
3. Add seed data in `dbt_project/seeds/` (if needed)
4. Update validation SQL for the lesson

### Running Tests

```bash
python manage.py test
```

## 📝 License

This project is for educational purposes.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues or questions, please create an issue in the repository.

---

**Happy Learning! 🎉**