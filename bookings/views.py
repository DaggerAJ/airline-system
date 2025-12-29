from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import BookingSerializer
from .models import Booking
from .services import BookingService

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    @action(detail=True, methods=['post'])
    def hold(self, request, pk=None):
        """Temporarily lock the seat[cite: 22]."""
        booking = BookingService.hold_seat(pk)
        return Response({"status": "Seat Locked", "held_at": booking.held_at})

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """Mocked payment result[cite: 23, 31]."""
        booking = self.get_object()
        success = request.data.get('success', True)
        
        if success:
            booking.transition_to(Booking.BookingStatus.PAYMENT_PENDING)
            booking.transition_to(Booking.BookingStatus.CONFIRMED)
            return Response({"status": "Confirmed"})
        return Response({"error": "Payment Failed"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """Process refund only once[cite: 25]."""
        booking = self.get_object()
        booking.transition_to(Booking.BookingStatus.REFUNDED)
        return Response({"status": "Refunded"})