import logging
from django.db import models
from django.utils import timezone

logger = logging.getLogger('booking_system')

class Booking(models.Model):
    class BookingStatus(models.TextChoices):
        INITIATED = 'INITIATED', 'Initiated' 
        SEAT_HELD = 'SEAT_HELD', 'Seat Held' 
        PAYMENT_PENDING = 'PAYMENT_PENDING', 'Payment Pending' 
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        EXPIRED = 'EXPIRED', 'Expired'
        REFUNDED = 'REFUNDED', 'Refunded'

    seat_id = models.CharField(max_length=10)
    status = models.CharField(
        max_length=20, 
        choices=BookingStatus.choices, 
        default=BookingStatus.INITIATED
    )
    held_at = models.DateTimeField(null=True, blank=True)

    def transition_to(self, new_status):
        """Strictly validates state transitions[cite: 13, 19]."""
        allowed = {
            self.BookingStatus.INITIATED: [self.BookingStatus.SEAT_HELD, self.BookingStatus.CANCELLED], 
            self.BookingStatus.SEAT_HELD: [self.BookingStatus.PAYMENT_PENDING, self.BookingStatus.EXPIRED], 
            self.BookingStatus.PAYMENT_PENDING: [self.BookingStatus.CONFIRMED, self.BookingStatus.CANCELLED],
            self.BookingStatus.CONFIRMED: [self.BookingStatus.CANCELLED, self.BookingStatus.REFUNDED],
        }

        if new_status not in allowed.get(self.status, []):
            logger.error(f"Illegal transition: {self.status} -> {new_status}")
            raise ValueError(f"Transition to {new_status} is not allowed from {self.status}.")

        self.status = new_status
        if new_status == self.BookingStatus.SEAT_HELD:
            self.held_at = timezone.now()
        
        self.save()
        logger.info(f"Booking {self.id} updated to {new_status}")