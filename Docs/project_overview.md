# 📘 Decode Data - Project Overview

## 🎯 Project Purpose

**Decode Data** is an interactive web-based learning platform designed to teach data transformation concepts using **dbt (data build tool)** through hands-on, practical exercises. The platform provides isolated workspaces for each learner, integrated with MotherDuck (cloud DuckDB) for data storage and querying.

## 🏗️ Architecture Overview

### Technology Stack

- **Backend Framework**: Django 4.2.7 (Python)
- **Database (App)**: SQLite (dev) / PostgreSQL (prod)
- **Database (Data)**: MotherDuck (DuckDB Cloud)
- **dbt**: dbt-duckdb 1.6.2
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Deployment**: Ready for Railway/Heroku/Render

### System Architecture

```
┌─────────────┐
│   Browser   │
│  (User UI)  │
└──────┬──────┘
       │
       │ HTTP/HTTPS
       ↓
┌──────────────────────────────────┐
│      Django Application          │
│  ┌────────────────────────────┐  │
│  │  Views (Controllers)       │  │
│  │  - Authentication          │  │
│  │  - Lesson Management       │  │
│  │  - Progress Tracking       │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  ┌────────────▼───────────────┐  │
│  │  DBT Manager               │  │
│  │  - Workspace Management    │  │
│  │  - Model Execution         │  │
│  │  - Seed Loading            │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  ┌────────────▼───────────────┐  │
│  │  Storage Layer             │  │
│  │  - MotherDuck Interface    │  │
│  │  - Query Execution         │  │
│  │  - Data Validation         │  │
│  └────────────┬───────────────┘  │
└───────────────┼───────────────────┘
                │
        ┌───────┴───────┐
        │               │
        ↓               ↓
┌──────────────┐  ┌──────────────┐
│   SQLite/    │  │  MotherDuck  │
│  PostgreSQL  │  │   (DuckDB)   │
│              │  │              │
│  - Users     │  │  - User      │
│  - Progress  │  │    Schemas   │
│  - Sessions  │  │  - dbt       │
│              │  │    Tables    │
└──────────────┘  └──────────────┘
```

## 📦 Core Components

### 1. User Management (`learning/models.py`)

**User Model**
- Extends Django's AbstractUser
- Auto-generates unique schema name for each user
- Tracks creation date

**LearnerProgress Model**
- Tracks progress percentage per lesson
- Stores completed steps
- Records executed models and queries
- Maintains quiz scores

**ModelEdit Model**
- Persists user's SQL model edits
- Enables resume functionality
- Tracks last modification time

**UserSession Model**
- Manages active sessions
- Links to dbt workspace path
- Tracks activity timestamps

### 2. DBT Manager (`learning/dbt_manager.py`)

**Responsibilities:**
- Create isolated dbt workspaces for each user/lesson
- Copy dbt project template to workspace
- Generate user-specific profiles.yml
- Execute dbt commands (run, seed, test)
- Load and save model files
- Create schemas in MotherDuck

**Key Methods:**
- `initialize_workspace()`: Sets up new dbt workspace
- `execute_models()`: Runs dbt models
- `run_seeds()`: Loads CSV data
- `save_model()`: Persists SQL changes
- `load_model()`: Retrieves model content

### 3. Storage Interface (`learning/storage.py`)

**Responsibilities:**
- Connect to MotherDuck
- Execute SQL queries
- Retrieve query results
- List available tables
- Validate lesson completion

**Key Methods:**
- `execute_query()`: Run SQL and return DataFrame
- `list_tables()`: Get tables in user schema
- `validate_output()`: Check completion criteria

### 4. View Controllers (`learning/views.py`)

**Authentication Views:**
- `login_view()`: User login
- `register_view()`: User registration
- `logout_view()`: User logout

**Learning Views:**
- `dashboard()`: Main dashboard with lesson cards
- `lesson_detail()`: Lesson overview and navigation
- `model_builder()`: Interactive SQL editor and executor
- `query_visualize()`: SQL query interface
- `progress_dashboard()`: Progress tracking

**API Endpoints:**
- `api_get_model_content()`: Load model SQL
- `api_validate_lesson()`: Check completion
- `api_test_dbt()`: Debug dbt execution

## 🎓 Lesson System

### Lesson Structure

Each lesson is defined in `LESSONS` list in `views.py`:

```python
{
    "id": "lesson_identifier",
    "title": "Display Title",
    "description": "Lesson description",
    "model_dir": "models/lesson_identifier",
    "validation": {
        "sql": "validation_query",
        "expected_min": minimum_tables
    }
}
```

### Lesson Components

1. **SQL Models** (`dbt_project/models/lesson_id/`)
   - dbt transformation logic
   - Jinja templating
   - Referencing between models

2. **Seed Data** (`dbt_project/seeds/lesson_id/`)
   - CSV files
   - Raw data for learning
   - Automatically loaded into schema

3. **Validation Logic**
   - SQL query to check completion
   - Minimum table count
   - Custom validation criteria

## 🔄 User Workflow

### 1. Registration & Login
```
User Register → Create Account → Generate Schema Name → Login → Dashboard
```

### 2. Lesson Initialization
```
Select Lesson → Lesson Detail → Model Builder → Initialize Workspace
  ↓
Create dbt Workspace → Copy Project Files → Create MotherDuck Schema → Ready
```

### 3. Learning Cycle
```
Load Seeds → Edit Models → Save Changes → Execute Models → View Results
     ↑                                                             ↓
     └─────────────────── Iterate ←──────────────────────────────┘
```

### 4. Progress Tracking
```
Complete Steps → Update Progress → Execute Models → Run Queries
       ↓              ↓                  ↓               ↓
   20% boost      Track in DB      List models    Increment count
```

## 🗂️ File Organization

### Django App Structure

```
learning/
├── models.py           # Database models
├── views.py            # Request handlers
├── forms.py            # Web forms
├── urls.py             # URL routing
├── admin.py            # Admin config
├── dbt_manager.py      # dbt operations
├── storage.py          # MotherDuck interface
└── templates/          # HTML templates
    ├── base.html       # Base layout
    ├── auth/           # Login/Register
    └── learning/       # Lesson pages
```

### dbt Project Structure

```
dbt_project/
├── dbt_project.yml     # dbt configuration
├── models/             # SQL transformations
│   ├── hello_dbt/
│   ├── cafe_chain/
│   └── energy_smart/
└── seeds/              # CSV data
    ├── hello_dbt/
    ├── cafe_chain/
    └── energy_smart/
```

## 🔐 Security Features

### Authentication
- Django's built-in authentication system
- Password hashing (PBKDF2)
- CSRF protection on all forms
- Login required decorators

### Workspace Isolation
- Each user gets unique MotherDuck schema
- Separate dbt workspace per user/lesson
- No cross-user data access

### Configuration
- Environment-based secrets (.env)
- SECRET_KEY for session security
- Secure token storage for MotherDuck

## 📊 Data Flow

### Creating a Model
```
1. User edits SQL in browser
2. AJAX call to save endpoint
3. SQL saved to database (ModelEdit)
4. SQL written to workspace file
5. Ready for execution
```

### Executing Models
```
1. User selects models
2. Form submission to execute endpoint
3. DBT Manager runs dbt command
4. dbt connects to MotherDuck
5. SQL executed in user schema
6. Results returned to user
7. Progress updated
```

### Querying Data
```
1. User writes SQL query
2. Form submission to query endpoint
3. Storage layer connects to MotherDuck
4. Query executed in user schema
5. Results converted to JSON
6. Table displayed in browser
```

## 🎨 Frontend Design

### UI Framework
- **Bootstrap 5**: Responsive layout
- **Bootstrap Icons**: Consistent iconography
- **Custom CSS**: Brand colors and styling

### Key Design Patterns
- Card-based layout for lessons
- Color-coded progress bars
- Icon-first navigation
- Responsive grid system
- Alert system for feedback

### JavaScript Functionality
- AJAX for model loading
- Form validation
- Confirmation dialogs
- Dynamic content updates

## 🚀 Deployment Considerations

### Environment Variables
```env
# Required
SECRET_KEY=<django-secret>
MOTHERDUCK_TOKEN=<token>

# Optional
DEBUG=False
DATABASE_URL=<postgres-url>
ALLOWED_HOSTS=your-domain.com
```

### Static Files
- Collected via `collectstatic`
- Served by WhiteNoise in production
- CDN for Bootstrap/Icons

### Database
- SQLite for development
- PostgreSQL for production
- MotherDuck for data warehouse

### Scaling Considerations
- Workspace cleanup for inactive users
- Async task queue for long-running dbt jobs
- Caching for frequently accessed data
- Connection pooling for MotherDuck

## 📈 Future Enhancements

### Planned Features
- [ ] Real-time collaboration
- [ ] Advanced visualizations
- [ ] Quiz/Assessment system
- [ ] Certificate generation
- [ ] Discussion forums
- [ ] Video tutorials
- [ ] Code diff viewer
- [ ] Export workspace
- [ ] Team/Organization support
- [ ] API for external integrations

### Technical Improvements
- [ ] Redis for caching
- [ ] Celery for async tasks
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline
- [ ] Automated testing suite
- [ ] Performance monitoring
- [ ] Error tracking (Sentry)

## 🧪 Testing Strategy

### Unit Tests
- Model methods
- Form validation
- Utility functions

### Integration Tests
- View workflows
- dbt execution
- MotherDuck queries

### End-to-End Tests
- User registration flow
- Lesson completion
- Model execution

## 📚 Documentation

### User Documentation# 📘 Decode Data - Project Overview

## 🎯 Project Purpose

**Decode Data** is an interactive web-based learning platform designed to teach data transformation concepts using **dbt (data build tool)** through hands-on, practical exercises. The platform provides isolated workspaces for each learner, integrated with MotherDuck (cloud DuckDB) for data storage and querying.

## 🏗️ Architecture Overview

### Technology Stack

- **Backend Framework**: Django 4.2.7 (Python)
- **Database (App)**: SQLite (dev) / PostgreSQL (prod)
- **Database (Data)**: MotherDuck (DuckDB Cloud)
- **dbt**: dbt-duckdb 1.6.2
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Deployment**: Ready for Railway/Heroku/Render

### System Architecture

```
┌─────────────┐
│   Browser   │
│  (User UI)  │
└──────┬──────┘
       │
       │ HTTP/HTTPS
       ↓
┌──────────────────────────────────┐
│      Django Application          │
│  ┌────────────────────────────┐  │
│  │  Views (Controllers)       │  │
│  │  - Authentication          │  │
│  │  - Lesson Management       │  │
│  │  - Progress Tracking       │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  ┌────────────▼───────────────┐  │
│  │  DBT Manager               │  │
│  │  - Workspace Management    │  │
│  │  - Model Execution         │  │
│  │  - Seed Loading            │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  ┌────────────▼───────────────┐  │
│  │  Storage Layer             │  │
│  │  - MotherDuck Interface    │  │
│  │  - Query Execution         │  │
│  │  - Data Validation         │  │
│  └────────────┬───────────────┘  │
└───────────────┼───────────────────┘
                │
        ┌───────┴───────┐
        │               │
        ↓               ↓
┌──────────────┐  ┌──────────────┐
│   SQLite/    │  │  MotherDuck  │
│  PostgreSQL  │  │   (DuckDB)   │
│              │  │              │
│  - Users     │  │  - User      │
│  - Progress  │  │    Schemas   │
│  - Sessions  │  │  - dbt       │
│              │  │    Tables    │
└──────────────┘  └──────────────┘
```

## 📦 Core Components

### 1. User Management (`learning/models.py`)

**User Model**
- Extends Django's AbstractUser
- Auto-generates unique schema name for each user
- Tracks creation date

**LearnerProgress Model**
- Tracks progress percentage per lesson
- Stores completed steps
- Records executed models and queries
- Maintains quiz scores

**ModelEdit Model**
- Persists user's SQL model edits
- Enables resume functionality
- Tracks last modification time

**UserSession Model**
- Manages active sessions
- Links to dbt workspace path
- Tracks activity timestamps

### 2. DBT Manager (`learning/dbt_manager.py`)

**Responsibilities:**
- Create isolated dbt workspaces for each user/lesson
- Copy dbt project template to workspace
- Generate user-specific profiles.yml
- Execute dbt commands (run, seed, test)
- Load and save model files
- Create schemas in MotherDuck

**Key Methods:**
- `initialize_workspace()`: Sets up new dbt workspace
- `execute_models()`: Runs dbt models
- `run_seeds()`: Loads CSV data
- `save_model()`: Persists SQL changes
- `load_model()`: Retrieves model content

### 3. Storage Interface (`learning/storage.py`)

**Responsibilities:**
- Connect to MotherDuck
- Execute SQL queries
- Retrieve query results
- List available tables
- Validate lesson completion

**Key Methods:**
- `execute_query()`: Run SQL and return DataFrame
- `list_tables()`: Get tables in user schema
- `validate_output()`: Check completion criteria

### 4. View Controllers (`learning/views.py`)

**Authentication Views:**
- `login_view()`: User login
- `register_view()`: User registration
- `logout_view()`: User logout

**Learning Views:**
- `dashboard()`: Main dashboard with lesson cards
- `lesson_detail()`: Lesson overview and navigation
- `model_builder()`: Interactive SQL editor and executor
- `query_visualize()`: SQL query interface
- `progress_dashboard()`: Progress tracking

**API Endpoints:**
- `api_get_model_content()`: Load model SQL
- `api_validate_lesson()`: Check completion
- `api_test_dbt()`: Debug dbt execution

## 🎓 Lesson System

### Lesson Structure

Each lesson is defined in `LESSONS` list in `views.py`:

```python
{
    "id": "lesson_identifier",
    "title": "Display Title",
    "description": "Lesson description",
    "model_dir": "models/lesson_identifier",
    "validation": {
        "sql": "validation_query",
        "expected_min": minimum_tables
    }
}
```

### Lesson Components

1. **SQL Models** (`dbt_project/models/lesson_id/`)
   - dbt transformation logic
   - Jinja templating
   - Referencing between models

2. **Seed Data** (`dbt_project/seeds/lesson_id/`)
   - CSV files
   - Raw data for learning
   - Automatically loaded into schema

3. **Validation Logic**
   - SQL query to check completion
   - Minimum table count
   - Custom validation criteria

## 🔄 User Workflow

### 1. Registration & Login
```
User Register → Create Account → Generate Schema Name → Login → Dashboard
```

### 2. Lesson Initialization
```
Select Lesson → Lesson Detail → Model Builder → Initialize Workspace
  ↓
Create dbt Workspace → Copy Project Files → Create MotherDuck Schema → Ready
```

### 3. Learning Cycle
```
Load Seeds → Edit Models → Save Changes → Execute Models → View Results
     ↑                                                             ↓
     └─────────────────── Iterate ←──────────────────────────────┘
```

### 4. Progress Tracking
```
Complete Steps → Update Progress → Execute Models → Run Queries
       ↓              ↓                  ↓               ↓
   20% boost      Track in DB      List models    Increment count
```

## 🗂️ File Organization

### Django App Structure

```
learning/
├── models.py           # Database models
├── views.py            # Request handlers
├── forms.py            # Web forms
├── urls.py             # URL routing
├── admin.py            # Admin config
├── dbt_manager.py      # dbt operations
├── storage.py          # MotherDuck interface
└── templates/          # HTML templates
    ├── base.html       # Base layout
    ├── auth/           # Login/Register
    └── learning/       # Lesson pages
```

### dbt Project Structure

```
dbt_project/
├── dbt_project.yml     # dbt configuration
├── models/             # SQL transformations
│   ├── hello_dbt/
│   ├── cafe_chain/
│   └── energy_smart/
└── seeds/              # CSV data
    ├── hello_dbt/
    ├── cafe_chain/
    └── energy_smart/
```

## 🔐 Security Features

### Authentication
- Django's built-in authentication system
- Password hashing (PBKDF2)
- CSRF protection on all forms
- Login required decorators

### Workspace Isolation
- Each user gets unique MotherDuck schema
- Separate dbt workspace per user/lesson
- No cross-user data access

### Configuration
- Environment-based secrets (.env)
- SECRET_KEY for session security
- Secure token storage for MotherDuck

## 📊 Data Flow

### Creating a Model
```
1. User edits SQL in browser
2. AJAX call to save endpoint
3. SQL saved to database (ModelEdit)
4. SQL written to workspace file
5. Ready for execution
```

### Executing Models
```
1. User selects models
2. Form submission to execute endpoint
3. DBT Manager runs dbt command
4. dbt connects to MotherDuck
5. SQL executed in user schema
6. Results returned to user
7. Progress updated
```

### Querying Data
```
1. User writes SQL query
2. Form submission to query endpoint
3. Storage layer connects to MotherDuck
4. Query executed in user schema
5. Results converted to JSON
6. Table displayed in browser
```

## 🎨 Frontend Design

### UI Framework
- **Bootstrap 5**: Responsive layout
- **Bootstrap Icons**: Consistent iconography
- **Custom CSS**: Brand colors and styling

### Key Design Patterns
- Card-based layout for lessons
- Color-coded progress bars
- Icon-first navigation
- Responsive grid system
- Alert system for feedback

### JavaScript Functionality
- AJAX for model loading
- Form validation
- Confirmation dialogs
- Dynamic content updates

## 🚀 Deployment Considerations

### Environment Variables
```env
# Required
SECRET_KEY=<django-secret>
MOTHERDUCK_TOKEN=<token>

# Optional
DEBUG=False
DATABASE_URL=<postgres-url>
ALLOWED_HOSTS=your-domain.com
```

### Static Files
- Collected via `collectstatic`
- Served by WhiteNoise in production
- CDN for Bootstrap/Icons

### Database
- SQLite for development
- PostgreSQL for production
- MotherDuck for data warehouse

### Scaling Considerations
- Workspace cleanup for inactive users
- Async task queue for long-running dbt jobs
- Caching for frequently accessed data
- Connection pooling for MotherDuck

## 📈 Future Enhancements

### Planned Features
- [ ] Real-time collaboration
- [ ] Advanced visualizations
- [ ] Quiz/Assessment system
- [ ] Certificate generation
- [ ] Discussion forums
- [ ] Video tutorials
- [ ] Code diff viewer
- [ ] Export workspace
- [ ] Team/Organization support
- [ ] API for external integrations

### Technical Improvements
- [ ] Redis for caching
- [ ] Celery for async tasks
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline
- [ ] Automated testing suite
- [ ] Performance monitoring
- [ ] Error tracking (Sentry)

## 🧪 Testing Strategy

### Unit Tests
- Model methods
- Form validation
- Utility functions

### Integration Tests
- View workflows
- dbt execution
- MotherDuck queries

### End-to-End Tests
- User registration flow
- Lesson completion
- Model execution

## 📚 Documentation

### User Documentation
- Getting Started Guide
- Lesson Tutorials
- FAQ
- Video Walkthroughs

### Developer Documentation
- Setup Guide (SETUP_GUIDE.md)
- Quick Start (QUICKSTART.md)
- API Reference
- Contributing Guidelines

## 🤝 Contributing

### Development Workflow
1. Fork repository
2. Create feature branch
3. Make changes
4. Write tests
5. Submit pull request

### Code Style
- PEP 8 for Python
- Black for formatting
- Type hints preferred
- Docstrings required

## 📞 Support

### Getting Help
- GitHub Issues
- Discussion Forum
- Email Support
- Documentation

---

**Built with ❤️ for the data community**# 📘 Decode Data - Project Overview

## 🎯 Project Purpose

**Decode Data** is an interactive web-based learning platform designed to teach data transformation concepts using **dbt (data build tool)** through hands-on, practical exercises. The platform provides isolated workspaces for each learner, integrated with MotherDuck (cloud DuckDB) for data storage and querying.

## 🏗️ Architecture Overview

### Technology Stack

- **Backend Framework**: Django 4.2.7 (Python)
- **Database (App)**: SQLite (dev) / PostgreSQL (prod)
- **Database (Data)**: MotherDuck (DuckDB Cloud)
- **dbt**: dbt-duckdb 1.6.2
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Deployment**: Ready for Railway/Heroku/Render

### System Architecture

```
┌─────────────┐
│   Browser   │
│  (User UI)  │
└──────┬──────┘
       │
       │ HTTP/HTTPS
       ↓
┌──────────────────────────────────┐
│      Django Application          │
│  ┌────────────────────────────┐  │
│  │  Views (Controllers)       │  │
│  │  - Authentication          │  │
│  │  - Lesson Management       │  │
│  │  - Progress Tracking       │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  ┌────────────▼───────────────┐  │
│  │  DBT Manager               │  │
│  │  - Workspace Management    │  │
│  │  - Model Execution         │  │
│  │  - Seed Loading            │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  ┌────────────▼───────────────┐  │
│  │  Storage Layer             │  │
│  │  - MotherDuck Interface    │  │
│  │  - Query Execution         │  │
│  │  - Data Validation         │  │
│  └────────────┬───────────────┘  │
└───────────────┼───────────────────┘
                │
        ┌───────┴───────┐
        │               │
        ↓               ↓
┌──────────────┐  ┌──────────────┐
│   SQLite/    │  │  MotherDuck  │
│  PostgreSQL  │  │   (DuckDB)   │
│              │  │              │
│  - Users     │  │  - User      │
│  - Progress  │  │    Schemas   │
│  - Sessions  │  │  - dbt       │
│              │  │    Tables    │
└──────────────┘  └──────────────┘
```

## 📦 Core Components

### 1. User Management (`learning/models.py`)

**User Model**
- Extends Django's AbstractUser
- Auto-generates unique schema name for each user
- Tracks creation date

**LearnerProgress Model**
- Tracks progress percentage per lesson
- Stores completed steps
- Records executed models and queries
- Maintains quiz scores

**ModelEdit Model**
- Persists user's SQL model edits
- Enables resume functionality
- Tracks last modification time

**UserSession Model**
- Manages active sessions
- Links to dbt workspace path
- Tracks activity timestamps

### 2. DBT Manager (`learning/dbt_manager.py`)

**Responsibilities:**
- Create isolated dbt workspaces for each user/lesson
- Copy dbt project template to workspace
- Generate user-specific profiles.yml
- Execute dbt commands (run, seed, test)
- Load and save model files
- Create schemas in MotherDuck

**Key Methods:**
- `initialize_workspace()`: Sets up new dbt workspace
- `execute_models()`: Runs dbt models
- `run_seeds()`: Loads CSV data
- `save_model()`: Persists SQL changes
- `load_model()`: Retrieves model content

### 3. Storage Interface (`learning/storage.py`)

**Responsibilities:**
- Connect to MotherDuck
- Execute SQL queries
- Retrieve query results
- List available tables
- Validate lesson completion

**Key Methods:**
- `execute_query()`: Run SQL and return DataFrame
- `list_tables()`: Get tables in user schema
- `validate_output()`: Check completion criteria

### 4. View Controllers (`learning/views.py`)

**Authentication Views:**
- `login_view()`: User login
- `register_view()`: User registration
- `logout_view()`: User logout

**Learning Views:**
- `dashboard()`: Main dashboard with lesson cards
- `lesson_detail()`: Lesson overview and navigation
- `model_builder()`: Interactive SQL editor and executor
- `query_visualize()`: SQL query interface
- `progress_dashboard()`: Progress tracking

**API Endpoints:**
- `api_get_model_content()`: Load model SQL
- `api_validate_lesson()`: Check completion
- `api_test_dbt()`: Debug dbt execution

## 🎓 Lesson System

### Lesson Structure

Each lesson is defined in `LESSONS` list in `views.py`:

```python
{
    "id": "lesson_identifier",
    "title": "Display Title",
    "description": "Lesson description",
    "model_dir": "models/lesson_identifier",
    "validation": {
        "sql": "validation_query",
        "expected_min": minimum_tables
    }
}
```

### Lesson Components

1. **SQL Models** (`dbt_project/models/lesson_id/`)
   - dbt transformation logic
   - Jinja templating
   - Referencing between models

2. **Seed Data** (`dbt_project/seeds/lesson_id/`)
   - CSV files
   - Raw data for learning
   - Automatically loaded into schema

3. **Validation Logic**
   - SQL query to check completion
   - Minimum table count
   - Custom validation criteria

## 🔄 User Workflow

### 1. Registration & Login
```
User Register → Create Account → Generate Schema Name → Login → Dashboard
```

### 2. Lesson Initialization
```
Select Lesson → Lesson Detail → Model Builder → Initialize Workspace
  ↓
Create dbt Workspace → Copy Project Files → Create MotherDuck Schema → Ready
```

### 3. Learning Cycle
```
Load Seeds → Edit Models → Save Changes → Execute Models → View Results
     ↑                                                             ↓
     └─────────────────── Iterate ←──────────────────────────────┘
```

### 4. Progress Tracking
```
Complete Steps → Update Progress → Execute Models → Run Queries
       ↓              ↓                  ↓               ↓
   20% boost      Track in DB      List models    Increment count
```

## 🗂️ File Organization

### Django App Structure

```
learning/
├── models.py           # Database models
├── views.py            # Request handlers
├── forms.py            # Web forms
├── urls.py             # URL routing
├── admin.py            # Admin config
├── dbt_manager.py      # dbt operations
├── storage.py          # MotherDuck interface
└── templates/          # HTML templates
    ├── base.html       # Base layout
    ├── auth/           # Login/Register
    └── learning/       # Lesson pages
```

### dbt Project Structure

```
dbt_project/
├── dbt_project.yml     # dbt configuration
├── models/             # SQL transformations
│   ├── hello_dbt/
│   ├── cafe_chain/
│   └── energy_smart/
└── seeds/              # CSV data
    ├── hello_dbt/
    ├── cafe_chain/
    └── energy_smart/
```

## 🔐 Security Features

### Authentication
- Django's built-in authentication system
- Password hashing (PBKDF2)
- CSRF protection on all forms
- Login required decorators

### Workspace Isolation
- Each user gets unique MotherDuck schema
- Separate dbt workspace per user/lesson
- No cross-user data access

### Configuration
- Environment-based secrets (.env)
- SECRET_KEY for session security
- Secure token storage for MotherDuck

## 📊 Data Flow

### Creating a Model
```
1. User edits SQL in browser
2. AJAX call to save endpoint
3. SQL saved to database (ModelEdit)
4. SQL written to workspace file
5. Ready for execution
```

### Executing Models
```
1. User selects models
2. Form submission to execute endpoint
3. DBT Manager runs dbt command
4. dbt connects to MotherDuck
5. SQL executed in user schema
6. Results returned to user
7. Progress updated
```

### Querying Data
```
1. User writes SQL query
2. Form submission to query endpoint
3. Storage layer connects to MotherDuck
4. Query executed in user schema
5. Results converted to JSON
6. Table displayed in browser
```

## 🎨 Frontend Design

### UI Framework
- **Bootstrap 5**: Responsive layout
- **Bootstrap Icons**: Consistent iconography
- **Custom CSS**: Brand colors and styling

### Key Design Patterns
- Card-based layout for lessons
- Color-coded progress bars
- Icon-first navigation
- Responsive grid system
- Alert system for feedback

### JavaScript Functionality
- AJAX for model loading
- Form validation
- Confirmation dialogs
- Dynamic content updates

## 🚀 Deployment Considerations

### Environment Variables
```env
# Required
SECRET_KEY=<django-secret>
MOTHERDUCK_TOKEN=<token>

# Optional
DEBUG=False
DATABASE_URL=<postgres-url>
ALLOWED_HOSTS=your-domain.com
```

### Static Files
- Collected via `collectstatic`
- Served by WhiteNoise in production
- CDN for Bootstrap/Icons

### Database
- SQLite for development
- PostgreSQL for production
- MotherDuck for data warehouse

### Scaling Considerations
- Workspace cleanup for inactive users
- Async task queue for long-running dbt jobs
- Caching for frequently accessed data
- Connection pooling for MotherDuck

## 📈 Future Enhancements

### Planned Features
- [ ] Real-time collaboration
- [ ] Advanced visualizations
- [ ] Quiz/Assessment system
- [ ] Certificate generation
- [ ] Discussion forums
- [ ] Video tutorials
- [ ] Code diff viewer
- [ ] Export workspace
- [ ] Team/Organization support
- [ ] API for external integrations

### Technical Improvements
- [ ] Redis for caching
- [ ] Celery for async tasks
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline
- [ ] Automated testing suite
- [ ] Performance monitoring
- [ ] Error tracking (Sentry)

## 🧪 Testing Strategy

### Unit Tests
- Model methods
- Form validation
- Utility functions

### Integration Tests
- View workflows
- dbt execution
- MotherDuck queries

### End-to-End Tests
- User registration flow
- Lesson completion
- Model execution

## 📚 Documentation

### User Documentation
- Getting Started Guide
- Lesson Tutorials
- FAQ
- Video Walkthroughs

### Developer Documentation
- Setup Guide (SETUP_GUIDE.md)
- Quick Start (QUICKSTART.md)
- API Reference
- Contributing Guidelines

## 🤝 Contributing

### Development Workflow
1. Fork repository
2. Create feature branch
3. Make changes
4. Write tests
5. Submit pull request

### Code Style
- PEP 8 for Python
- Black for formatting
- Type hints preferred
- Docstrings required

## 📞 Support

### Getting Help
- GitHub Issues
- Discussion Forum
- Email Support
- Documentation

---

**Built with ❤️ for the data community**
- Getting Started Guide
- Lesson Tutorials
- FAQ
- Video Walkthroughs

### Developer Documentation
- Setup Guide (SETUP_GUIDE.md)
- Quick Start (QUICKSTART.md)
- API Reference
- Contributing Guidelines

## 🤝 Contributing

### Development Workflow
1. Fork repository
2. Create feature branch
3. Make changes
4. Write tests
5. Submit pull request

### Code Style
- PEP 8 for Python
- Black for formatting
- Type hints preferred
- Docstrings required

## 📞 Support

### Getting Help
- GitHub Issues
- Discussion Forum
- Email Support
- Documentation

---

**Built with ❤️ for the data community**