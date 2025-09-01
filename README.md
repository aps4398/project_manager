# Project Management System

A comprehensive Django-based project management system for teams to collaborate on projects and tasks.

## Features

- **User Management**: Custom user model with profiles and authentication
- **Project Tracking**: Create and manage projects with team members
- **Task Management**: Assign tasks with priorities and due dates
- **Team Collaboration**: Comment on tasks and share files
- **Dashboard**: Overview of projects, tasks, and recent activity
- **REST API**: Full API endpoints for integration
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

- Django 4.2.7
- PostgreSQL (production) / SQLite (development)
- Bootstrap 5
- Gunicorn
- Nginx
- Docker

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

cp .env.example .env
# Edit .env with your configuration

python manage.py migrate

python manage.py createsuperuser

python manage.py runserver
