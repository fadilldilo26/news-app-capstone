📰 NewsApp Capstone Project
A comprehensive Django-based news management platform featuring role-based access control, publisher workflows, and content curation. This project was developed as part of the HyperionDev Software Engineering Capstone.
✨ Key Features
Role-Based Access Control: Distinct dashboards and permissions for Readers, Journalists, Editors, and Publishers.
Publisher Workflow: Dedicated registration flow that automatically creates a publication and allows staff assignment.
Editorial Pipeline: Journalists submit articles → Editors review and approve → Approved articles appear in newsletters.
Newsletter Curation: Editors and Journalists can bundle approved articles into curated newsletters.
REST API: Full CRUD endpoints for articles, newsletters, publishers, and users using Django REST Framework.
🛠️ Tech Stack
Backend: Python 3.x, Django 4.2+
API: Django REST Framework (DRF)
Database: SQLite (Default) / MariaDB (Configurable)
Frontend: HTML5, Bootstrap 5, Django Templates
🚀 Installation & Setup
1.
Clone the repository:
bash
1
2
git clone https://github.com/fadilldilo26/news-app-capstone.git
    cd news-app-capstone
2.
Create and activate a virtual environment:
bash
1
2
3
4
5
python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
3.
Install dependencies:
bash
1
pip install -r requirements.txt
4.
Run migrations:
bash
1
2
python manage.py makemigrations
    python manage.py migrate
5.
Start the development server: python manage.py runserver
bash
1
python manage.py runserver
