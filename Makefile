# --- Docker Commands ---

build:
	docker-compose build

up:
	docker-compose up

down:
	docker-compose down

# --- Django & Celery Shortcuts ---

migrate:
	docker-compose exec web python manage.py migrate

test:
	docker-compose exec web python manage.py test bookings

shell:
	docker-compose exec web python manage.py shell

# --- Setup & Cleanup ---

setup:
	docker-compose up --build -d
	docker-compose exec web python manage.py migrate
	@echo "Project is running at http://localhost:8000/api/bookings/"

logs-worker:
	docker-compose logs -f worker

clean:
	docker-compose down -v
	find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find . -name "*.pyc" -delete