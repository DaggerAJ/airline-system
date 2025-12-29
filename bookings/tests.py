from django.test import TransactionTestCase
from .models import Booking
from .services import BookingService
from .tasks import expire_seat_hold_task
import threading

class BookingSystemTests(TransactionTestCase):

    def setUp(self):
        """Initialize a base booking for tests."""
        self.booking = Booking.objects.create(seat_id="A1")

    # --- STATE MACHINE TESTS ---

    def test_initial_state(self):
        """Verify booking starts in INITIATED state."""
        self.assertEqual(self.booking.status, Booking.BookingStatus.INITIATED)

    def test_valid_transition_flow(self):
        """Test the happy path: INITIATED -> SEAT_HELD -> PAYMENT_PENDING -> CONFIRMED."""
        self.booking.transition_to(Booking.BookingStatus.SEAT_HELD)
        self.assertEqual(self.booking.status, Booking.BookingStatus.SEAT_HELD)

        self.booking.transition_to(Booking.BookingStatus.PAYMENT_PENDING)
        self.booking.transition_to(Booking.BookingStatus.CONFIRMED)
        self.assertEqual(self.booking.status, Booking.BookingStatus.CONFIRMED)

    def test_invalid_transition(self):
        """Verify that skipping states (e.g., INITIATED to CONFIRMED) is rejected."""
        with self.assertRaises(ValueError):
            self.booking.transition_to(Booking.BookingStatus.CONFIRMED)

    def test_refund_logic(self):
        """Ensure refunds only occur from CONFIRMED and only once."""
        self.booking.status = Booking.BookingStatus.CONFIRMED
        self.booking.save()

        # First refund attempt
        self.booking.transition_to(Booking.BookingStatus.REFUNDED)
        self.assertEqual(self.booking.status, Booking.BookingStatus.REFUNDED)

        # Second refund attempt should fail
        with self.assertRaises(ValueError):
            self.booking.transition_to(Booking.BookingStatus.REFUNDED)

    # --- CELERY / EXPIRY TESTS ---

    def test_auto_expiry_logic(self):
        """Test the 10-minute expiry requirement by calling the task directly."""
        BookingService.hold_seat(self.booking.id)
        
        # Manually trigger the background task logic
        expire_seat_hold_task(self.booking.id)

        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.BookingStatus.EXPIRED)

    def test_payment_prevents_expiry(self):
        """Ensure the expiry task does not cancel a booking that was paid for."""
        # 1. You MUST hold the seat first to move from INITIATED -> SEAT_HELD
        BookingService.hold_seat(self.booking.id)
        self.booking.refresh_from_db() # Sync the state to the test object
        
        # 2. Now the state is SEAT_HELD, so these transitions are allowed
        self.booking.transition_to(Booking.BookingStatus.PAYMENT_PENDING)
        self.booking.transition_to(Booking.BookingStatus.CONFIRMED)
        
        # 3. The expiry task runs (simulating the 10-min mark)
        expire_seat_hold_task(self.booking.id)

        # Status should remain CONFIRMED, not change to EXPIRED
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.BookingStatus.CONFIRMED)

    # --- CONCURRENCY / LOCKING TESTS ---

    def test_concurrent_seat_locking(self):
        """Simulate two requests trying to 'hold' the same seat simultaneously."""
        results = []

        def attempt_hold():
            try:
                # Calls select_for_update() inside the service
                BookingService.hold_seat(self.booking.id)
                results.append("SUCCESS")
            except Exception as e:
                results.append(f"FAILED: {str(e)}")

        thread1 = threading.Thread(target=attempt_hold)
        thread2 = threading.Thread(target=attempt_hold)

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        # Verify one request succeeded and the other was blocked
        self.assertIn("SUCCESS", results)
        self.assertTrue(any("FAILED" in r for r in results))