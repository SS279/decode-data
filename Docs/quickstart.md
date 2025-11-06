# 🚀 Quick Start Guide

Get up and running with Decode Data in 5 minutes!

## ⚡ Super Quick Setup

### Step 1: Install & Setup (2 minutes)

```bash
# Clone and navigate
cd decode_data_project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure (1 minute)

```bash
# Copy environment file
cp .env.example .env
```

Edit `.env` and add:
```env
SECRET_KEY=django-insecure-change-this-to-something-random
DEBUG=True
MOTHERDUCK_TOKEN=your_token_here
```

### Step 3: Initialize Database (1 minute)

```bash
# Run migrations
python manage.py migrate

# Create admin user (optional)
python manage.py createsuperuser
```

### Step 4: Start Server (1 minute)

```bash
# Run server
python manage.py runserver
```

Visit: **http://localhost:8000**

## 🎯 First Time User Flow

1. **Register** → Create your account
2. **Dashboard** → See available lessons
3. **Choose a Lesson** → Click "Start Lesson"
4. **Model Builder** → Click "Initialize Workspace"
5. **Load Seeds** → Click "Run Seeds"
6. **Edit & Execute** → Select a model, edit SQL, execute!

## 📋 Checklist

Before starting, make sure you have:

- [ ] Python 3.9+ installed
- [ ] MotherDuck account created
- [ ] MotherDuck token copied
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] .env file configured
- [ ] Database migrated
- [ ] dbt_project directory created (with sample models)

## 🐛 Quick Fixes

**Problem**: Can't connect to MotherDuck
**Solution**: Check your token in `.env` file

**Problem**: dbt command not found
**Solution**: `pip install dbt-duckdb`

**Problem**: No models showing
**Solution**: Create `dbt_project/` directory with models

## 📚 Next Steps

- Read the full [README.md](README.md)
- Explore the Model Builder
- Try writing SQL queries
- Check your progress dashboard

## 💡 Pro Tips

1. **Use SQLite for local development** (no DATABASE_URL needed)
2. **Initialize workspace once per lesson** (saves time)
3. **Save models before executing** (avoid losing changes)
4. **Check messages** for execution feedback

---

Need help? Check [README.md](README.md) for detailed documentation!