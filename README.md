# goldenhands2

A Django web application for organizing events with automated task assignment and email invitations.

## Features

- Create an event with occasion, date, and location
- Add attendees by name and email
- Define tasks that get randomly assigned to attendees
- Send email invitations to the organizer and all attendees with their assigned task

## Tech Stack

- Python / Django
- PostgreSQL
- Docker & Docker Compose
- Gunicorn + WhiteNoise for production

## Local Development

Requires Docker and Docker Compose.

1. Create a `.env.dev` file with your environment variables (database URL, email settings, etc.)
2. Build and start the containers:

```bash
docker-compose up --build
```

3. Run migrations:

```bash
docker-compose exec goldenhands python manage.py migrate
```

4. The app will be available at [http://localhost:8000](http://localhost:8000)

## Running Tests

```bash
pytest
```

## Project Structure

```
goldenhands/     # Django project settings and URL configuration
invitations/     # Main app — models, views, forms, templates
```
