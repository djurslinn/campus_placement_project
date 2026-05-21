# Campus Placement Training System - Phase 1

## Project Overview
A Django-based Campus Placement Training System with role-based authentication for students and coordinators.

## Features (Phase 1)
- User registration for students and coordinators
- Email-based authentication
- Role-based dashboards
- Placeholder UI for future features:
  - Aptitude Test
  - Mock Interview
  - Resume Builder
  - Placement Drives

## Tech Stack
- Python 3
- Django 4.2.7
- SQLite Database
- HTML/CSS

## Project Structure
```
campus_placement/
├── campus_placement/          # Main project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                  # User authentication app
│   ├── __init__.py
│   ├── models.py             # Custom User model
│   ├── views.py              # Registration and dashboard views
│   ├── urls.py               # URL routing
│   ├── forms.py              # Registration forms
│   ├── admin.py              # Admin configuration
│   └── apps.py
├── core/                      # Landing page and login
│   ├── __init__.py
│   ├── views.py              # Index and logout views
│   ├── urls.py               # URL routing
│   └── apps.py
├── templates/                 # HTML templates
│   ├── index.html
│   ├── student_register.html
│   ├── coordinator_register.html
│   ├── student_dashboard.html
│   └── coordinator_dashboard.html
├── static/                    # Static files
│   └── style.css
├── manage.py
├── requirements.txt
└── README.md
```

## Setup Instructions

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```
Follow the prompts to create an admin account.

### 5. Run Development Server (All Services)
The project now includes an automated command to start both the Django server and the AI Microservices with a single command.

**Option A: Recommended (All-in-one)**
```bash
python manage.py runall
```

**Option B: Separate Commands**
If you prefer running them in separate terminals:
- Django: `python manage.py runserver`
- ATS AI Service: `cd ats-ai-service && uvicorn main:app --port 8001`

**Option C: Windows Shortcut**
Double-click `run_dev.bat` in the project root.

### 6. Access the Application
- **Home Page/Login**: http://127.0.0.1:8000/
- **Student Registration**: http://127.0.0.1:8000/register/student/
- **Coordinator Registration**: http://127.0.0.1:8000/register/coordinator/
- **Admin Panel**: http://127.0.0.1:8000/admin/

## User Roles

### Student
- Can register with: Name, Email, Department, Year, Password
- Access to: Student Dashboard with placeholder features
- Dashboard URL: `/student/dashboard/`

### Coordinator
- Can register with: Name, Email, Password
- Access to: Coordinator Dashboard with placeholder features
- Dashboard URL: `/coordinator/dashboard/`

## Authentication Flow
1. Users land on index page (login page)
2. Register as Student or Coordinator
3. Login with email and password
4. Redirected to role-specific dashboard
5. Dashboard access is protected and role-checked

## Security Features
- Custom User model with role field
- Login required decorators
- Role-based access control
- Cross-role access prevention
- CSRF protection
- Password validation

## Future Features (Not Implemented in Phase 1)
- Aptitude Test functionality
- Mock Interview system
- Resume Builder
- Placement Drive management
- Student management for coordinators

## Notes
- This is Phase 1: Basic authentication and dashboard structure only
- All advanced features are placeholders in the UI
- SQLite database is used (db.sqlite3)
- Static files are served from /static/ directory
- Templates use Django template language

## Testing Accounts
After setup, create test accounts:
1. Register a student account
2. Register a coordinator account
3. Test login and role-based redirection

## Troubleshooting
- If migrations fail: Delete db.sqlite3 and try again
- If static files don't load: Check STATIC_URL in settings.py
- If login fails: Verify email and password are correct

## Development Commands
```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run ALL services (Django + Microservices)
python manage.py runall

# Run development server (Django only)
python manage.py runserver

# Access Django shell
python manage.py shell
```

## License
Educational project for campus placement management.
