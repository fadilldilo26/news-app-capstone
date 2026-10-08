# NewsApp Capstone Project

A full-stack Django news application featuring role-based access control for Publishers, Editors, Journalists, and Readers. Built with Django 4.2, Bootstrap 5, and MariaDB/MySQL.

## 🚀 Features Implemented
- **Publisher Dashboard**: Setup publication, manage staff assignments (Editors/Journalists)
- **Editor Workflow**: Review pending articles, approve/reject submissions via dedicated queue
- **Journalist Tools**: Create/Edit/Delete articles; link to publications or publish independently
- **Reader Experience**: Browse approved articles, subscribe to publishers/journalists, personalized "My Feed"
- **REST API**: Full CRUD endpoints for articles, newsletters, and publishers using DRF

## 🛠️ Tech Stack
- **Backend**: Django 4.2.30, Django REST Framework
- **Database**: MariaDB / MySQL
- **Frontend**: Bootstrap 5, HTML5/CSS3
- **Version Control**: Git & GitHub

## ⚙️ Setup Instructions

### 1. Prerequisites
Ensure you have Python 3.10+ and MariaDB/MySQL installed on your system.

### 2. Database Setup (MariaDB/MySQL)
Before running migrations, you must create the database manually:

1. Open your terminal/command prompt.
2. Log in to your MySQL/MariaDB server:
```bash
    mysql -u root -p
```
3. Enter your root password when prompted.
4. Create the database for the project:
```sql
    CREATE DATABASE news_app_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    EXIT;
```

### 3. Project Configuration
1. Clone the repository:
```bash
    git clone https://github.com/fadildilo26/news-app-capstone.git
    cd news-app-capstone-main
```

2. Create and activate a virtual environment:
```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
```

3. Install dependencies:
```bash
    pip install -r requirements.txt
```

4. **Update Database Credentials**:
    Open `news_project/settings.py` and update the `DATABASES` section with your local credentials:
```python
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql', # or mariadb
            'NAME': 'news_app_db',
            'USER': 'root', # Your DB username
            'PASSWORD': 'your_password', # Your DB password
            'HOST': 'localhost',
            'PORT': '3306',
        }
    }
```

### 4. Run Migrations & Start Server
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
Visit: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Test Accounts & Workflow

*Note: The database is empty after initial migration. Use the script below to populate test accounts.*

### Quick Setup Script
Run this in your terminal to create all test users instantly:
```bash
python manage.py shell
```
```python
from news.models import CustomUser

# Create Publisher
CustomUser.objects.create_user('testpub', password='Lets@test23', role='publisher')

# Create Editor
CustomUser.objects.create_user('Mezzy', password='Faadhil@!26', role='editor')

# Create Journalist
CustomUser.objects.create_user('Ami', password='Aameez123@!', role='journalist')

# Create Reader
CustomUser.objects.create_user('testrun', password='Reader@2024!', role='reader')

exit()
```

### Login Credentials
| Username | Password | Role | Key Actions |
| :--- | :--- | :--- | :--- |
| `testpub` | `Lets@test23` | Publisher | Setup Publication, Assign Staff |
| `Mezzy` | `Faadhil@!26` | Editor | Review Articles, Approve/Reject |
| `Ami` | `Aameez123@!` | Journalist | Write Articles, Publish Independently |
| `testrun` | `Reader@2024!` | Reader | Subscribe, View "My Feed" |

### Recommended Testing Workflow
1. **Publisher**: Login as `testpub` → Click "Setup Publication" → Create "TestPub News" → Assign `Mezzy` (Editor) & `Ami` (Journalist).
2. **Journalist**: Login as `Ami` → "Write New Article" → Select "TestPub News" → Submit.
3. **Editor**: Login as `Mezzy` → "Review Articles" → Click "Approve" on pending article.
4. **Reader**: Login as `testrun` → Go to "Subscriptions" → Subscribe to "TestPub News" → Check "My Feed".

## 📁 Project Structure

news-app-capstone-main/
├── news/ # Main Application
│ ├── models.py # CustomUser, Publisher, Article, Newsletter
│ ├── views.py # Web Views + DRF ViewSets
│ ├── urls.py # URL Routing
│ ├── serializers.py # API Serializers
│ └── templates/news/ # HTML Templates
├── news_project/ # Project Settings (settings.py, wsgi.py)
├── manage.py
├── requirements.txt
└── README.md

## 🔒 Security Notes
- All forms include CSRF protection tokens.
- Role-based access control enforced in views (`@login_required`, role checks).
- Session authentication for web interface; Token auth for API endpoints.
- Sensitive settings (SECRET_KEY, DB_PASSWORD) should be moved to environment variables for production.
