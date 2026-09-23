# NewsApp Capstone Project

A full-stack Django news application with role-based access control, RESTful API, and MariaDB backend.

## Prerequisites
- Python 3.10+
- Git
- XAMPP (or standalone MariaDB 10.4+)

## Installation & Setup

### 1. Clone the Repository
Open your terminal and run:
```bash
git clone https://github.com/YOUR_USERNAME/news-app-capstone.git
cd news-app-capstone
```

### 2. Create Virtual Environment
Create a fresh virtual environment inside the project folder:
```bash
python -m venv venv
```

### 3. Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```
**Mac/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies
Install all required packages from requirements.txt:
```bash
pip install -r requirements.txt
```

### 5. Setup MariaDB Database
1. Start Apache and MySQL in XAMPP Control Panel.
2. Open phpMyAdmin at http://localhost/phpmyadmin
3. Click "SQL" tab and run:
```sql
CREATE DATABASE news_app_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'NewsApp2026!';
GRANT ALL PRIVILEGES ON news_app_db.* TO 'news_user'@'localhost';
FLUSH PRIVILEGES;
```

### 6. Configure Database Credentials
Open `news_project/settings.py` and verify the DATABASES section matches your credentials:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'news_app_db',
        'USER': 'news_user',
        'PASSWORD': 'NewsApp2026!',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 7. Run Migrations
Apply database migrations to create tables:
```bash
python manage.py migrate
```

### 8. Create Superuser
Create an admin account to access the site:
```bash
python manage.py createsuperuser
```

### 9. Start Development Server
```bash
python manage.py runserver
```
Visit http://127.0.0.1:8000/ in your browser.

## Features
- Custom User Model with roles (Reader, Editor, Journalist)
- RESTful API with Token Authentication
- Article approval workflow with Django signals
- Email notifications to subscribers
- Web UI for editors to review/approve articles
- MariaDB database backend

## API Endpoints
- `POST /api/token/` - Obtain authentication token
- `GET /api/articles/` - List approved articles
- `POST /api/articles/` - Create article (Journalist/Editor only)
- `POST /api/articles/<id>/approve/` - Approve article (Editor only)
- `GET /api/articles/subscribed/` - Get subscribed articles (Reader only)

## Testing
Run unit tests:
```bash
python manage.py test news
```

## Note on User Registration
This project uses a custom login system. User registration is handled via Django Admin (`/admin/`) or API. To create new users, use `python manage.py createsuperuser` or the Django Admin panel.