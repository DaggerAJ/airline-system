from celery import shared_task
from .models import Booking

@shared_task
def expire_seat_hold_task(booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        if booking.status == Booking.BookingStatus.SEAT_HELD:
            booking.transition_to(Booking.BookingStatus.EXPIRED)
    except Booking.DoesNotExist:
        pass