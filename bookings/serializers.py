from rest_framework import serializers
from .models import Booking

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        # Include all relevant fields for the API
        fields = ['id', 'seat_id', 'status', 'held_at']
        # Ensure status and held_at are read-only to protect the state machine
        read_only_fields = ['status', 'held_at']

    def validate_seat_id(self, value):
        """Custom validation for the seat ID."""
        if not value:
            raise serializers.ValidationError("Seat ID cannot be empty.")
        return value