# Airline Seat Booking System
This is a Django REST Framework (DRF) backend designed to handle the seat booking lifecycle. It features a strict state machine, concurrency handling for seat locks, and an asynchronous background task system for seat expiration.
## 1. Setup & Installation
The project is fully containerized. You only need Docker and make installed on your machine.
### One-Step Setup
Bash
    ```make setup```
This will build the containers, start the services (Django, Redis, Celery), and run the database migrations.Manual CommandsIf you prefer running commands individually:Build/Start: docker-compose up --buildMigrations: docker-compose exec web python manage.py migrateTests: docker-compose exec web python manage.py test bookings
## 2. Technical Architecture
State Machine LogicTo ensure data integrity, the system enforces a strict transition flow. You cannot skip steps (e.g., you cannot pay for a seat that hasn't been held).The Path: INITIATED → SEAT_HELD → PAYMENT_PENDING → CONFIRMED → REFUNDEDConcurrency & LockingWe use select_for_update() within a database transaction during the hold action. This prevents a "race condition" where two users might attempt to lock the same seat at the same microsecond. The second request will wait or fail rather than creating a duplicate hold.Background Expiry (Celery + Redis)When a seat is moved to SEAT_HELD, a Celery task is dispatched with a ETA (countdown) of 10 minutes.Logic: The task checks the status after 10 minutes. If the booking is still SEAT_HELD, it moves it to EXPIRED.Safety: If the status is already CONFIRMED, the task exits without making changes.
## 3. API EndpointsMethod
EndpointDescription
- POST/api/bookings/Create a new booking (starts as INITIATED).
- POST/api/bookings/{id}/hold/Places a 10-minute lock on the seat.
- POST/api/bookings/{id}/pay/Finalizes the booking. Expects {"success": true}.
- POST/api/bookings/{id}/refund/Reverses a confirmed booking.GET/api/bookings/List all bookings and their current statuses.
## 4. Verification Guide
Testing the 10-Minute ExpiryCreate a booking and trigger the /hold/ endpoint.Run make logs-worker to see the Celery worker receive the task.Wait for the timeout (or adjust the countdown in services.py for a quicker test).Refresh the booking status via a GET request to see it move to EXPIRED.Running the Test SuiteThe project includes 7 core test cases covering:Valid/Invalid state transitions.Concurrent locking attempts.Expiry logic safety.Bashmake test
## 5. Development NotesEnvironment: 
Developed using Python 3.9, Django 4.2, and Redis 7.Port Mapping: The web server runs on localhost:8000. Ensure this port is not occupied by local processes or AirPlay Receiver.