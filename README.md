🎓 Learnova AI: Advanced Mentorship & Course Generation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Learnova is a high-performance, AI-driven learning platform. It leverages the Gemini 3 Flash model to generate structured curriculum skeletons, interactive quizzes, and personalized tutoring sessions. Built with Flask and fully containerized, it ensures a seamless bridge between complex AI schemas and a user-friendly educational experience.

🚀 Key Features
Structured AI Generation: Uses Pydantic v2 schemas (CourseSkeletonLite, QuizListLite) to ensure AI responses are technically valid and ready for the UI.

Dynamic Tutoring: Context-aware chat system that switches between a General Mentor and a Chapter-specific Tutor.

Voice-First UX: Integrated Speech-to-Text (STT) and Text-to-Speech (TTS) with a modern "Pill" UI design.

Background Tasks: Powered by Flask-Executor, handling AI generations and emails without blocking the main user interface.

Scalable Architecture: Redis-backed rate limiting to protect API quotas and maintain system stability.

🏗 Curriculum & Personalization Constraints
To maintain high educational standards, the platform strictly enforces:

Minimum Subjects: Every course must have at least 5 subjects/projects.

Minimum Sessions: Each subject must contain at least 5 chapters/sessions.

AI Validation: All generation logic is validated through a smart_fix_schema utility to prevent JSON formatting errors.

📦 Installation & Setup
1. Environment Configuration

Create a .env file in the root directory and populate it with your credentials:

Code snippet
# Server Config
FLASK_RUN_PORT=7000
SECRET_KEY=9e98192778... (your-secure-hex)

# AI Service
GEMINI_API_KEY=AIzaSy... (your-google-api-key)
OPEN_AI_API_KEY=sk-proj... (fallback-key)

# Docker Database (Points to the 'db' service)
DATABASE_URL=postgresql://my_user:my_password@my_host:5432/my_db
REDIS_URL=redis://redis:6379/0

# Mail Configuration
MAIL_SERVER=smtpout.secureserver.net
MAIL_PORT=465
MAIL_USE_TLS=False
MAIL_USE_SSL=True
MAIL_USERNAME=your_mail_username
MAIL_PASSWORD=your_mail_password
MAIL_FROM=your_mail_username
MAIL_FROM_NAME=Learnova
ADMIN_EMAIL=your_admin_email
2. Run with Docker (Recommended)

This method handles PostgreSQL and Redis setup automatically.

Bash
# Build and start the infrastructure
docker-compose up --build -d

# Initialize the database within the container
docker-compose exec web flask db upgrade
3. Local Development (Manual)

If you prefer running without Docker, ensure Postgres and Redis are installed on your machine.

Bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python wsgi.py

4. Run Tests

Install the development dependencies and run the test suite from the project root:

```bash
pip install -r requirements-dev.txt
pytest
```

The shared fixtures in `tests/conftest.py` provide an isolated SQLite-backed Flask app, test client, CLI runner, and database extension for tests.

📂 Project Structure
app/: Main application logic.

models/: SQLAlchemy database models (Users, Courses, Chat).

learning/: Gemini AI logic, Pydantic schemas, and tutor personas.

static/: CSS, Modern JS (Voice recognition logic), and user uploads.

config.py: Centralized configuration for Development and Production.

wsgi.py: Entry point that initializes the Flask factory.

Dockerfile & docker-compose.yml: Full container orchestration logic.

🧪 Maintenance & Maintenance
Task	Command
View Live Logs	docker-compose logs -f web
Stop All Services	docker-compose down
Access DB Shell	docker-compose exec db psql -U tushar -d learnova_db
Reset Database	flask db downgrade && flask db upgrade
📝 Troubleshooting
Redis Error: If the Redis container is down, the system uses fakeredis to avoid crashing, but rate limits will not persist across restarts.

DB Connection: Ensure your DATABASE_URL uses @db:5432 when in Docker and @localhost:5432 when running locally.