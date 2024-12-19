from rest_framework import serializers
from .models import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

# class EventSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Event
#         fields = '__all__'
class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ['id', 'images']
        extra_kwargs = {'images': {'required': False}}  
class EventSerializer(serializers.ModelSerializer):
    images = EventImageSerializer(many=True)  # Serialize related images

    class Meta:
        model = Event
        fields = ['id', 'eventName', 'eventTiming', 'eventCapacity', 'eventPriceAdult', 'eventPriceChild', 
                  'eventStatus', 'eventDisplay', 'eventActive', 'images']
class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

class MonitoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monitoring
        fields = '__all__'

class ModifiedTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username

        # Determine user type based on group membership
        if user.groups.filter(name='Employees').exists():
            token['user_type'] = 'employee'
        elif user.is_superuser:
            token['user_type'] = 'admin'
        else:
            token['user_type'] = 'unknown'

        return token

class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Access the user through the refresh token
        refresh = self.token_class(attrs['refresh'])
        user = self.context['request'].user or refresh['user_id']

        # Add custom claims
        data['username'] = user.username  # Assuming user info exists in request/user or token claim
        if user.groups.filter(name='Employees').exists():
            data['user_type'] = 'employee'
        elif user.is_superuser:
            data['user_type'] = 'admin'
        else:
            data['user_type'] = 'unknown'

        return data