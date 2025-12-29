from django.db import transaction
from .models import Booking
from .tasks import expire_seat_hold_task

class BookingService:
    @staticmethod
    def hold_seat(booking_id):
        with transaction.atomic():
            # Lock the row for this booking 
            booking = Booking.objects.select_for_update().get(id=booking_id)
            booking.transition_to(Booking.BookingStatus.SEAT_HELD)
            
            # Schedule 10-minute expiry 
            expire_seat_hold_task.apply_async((booking.id,), countdown=600)
            return booking