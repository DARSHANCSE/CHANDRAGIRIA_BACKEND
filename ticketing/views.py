from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from .models import Event, Booking, Monitoring,EventImage
from .serializers import EventSerializer, BookingSerializer, MonitoringSerializer,EventImageSerializer
from .utils import createRazorpayClient
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import ModifiedTokenObtainPairSerializer,CustomTokenRefreshSerializer
from datetime import datetime
from rest_framework.exceptions import ValidationError
import razorpay
import logging,json 
from rest_framework.decorators import action
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser




razorpay_client = createRazorpayClient(settings.RZP_ID, settings.RZP_SECRET_KEY)

# LoginView using JWT
class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self,r):
        username=r.data.get("username")
        password=r.data.get("password")
        # print(username,password)
        user = authenticate(username=username, password=password)
        if user:
            Token = ModifiedTokenObtainPairSerializer.get_token(user)
            access_token = Token.access_token
            print("Aaaaaa",access_token,Token)
            return Response({
                "Token": str(Token),
                "access": str(access_token),
            }, status=status.HTTP_200_OK)  
        return Response(status=status.HTTP_401_UNAUTHORIZED)
 
        
    

# LogoutView using JWT
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes=[AllowAny]   
    def post(self, request):
        try:
            # Retrieve the token from the request data
            refresh_token = request.data.get("token")
            if not refresh_token:
                raise ValidationError("Refresh token is required.")

            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)
        except ValidationError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "An error occurred during logout."}, status=status.HTTP_400_BAD_REQUEST)

# CreateOrder for Razorpay
class CreateOrder(APIView):
    def post(self, request):
        amount = request.data['amount']
        order_data = {'amount': int(amount),
            'currency': 'INR',
            'payment_capture':0}
        order = razorpay_client.order.create(order_data)
        print(order.keys())
        return Response({'order_id': order['id'], 'key': settings.RZP_ID}, status=status.HTTP_200_OK)

class PaymentCapture(APIView):
    def post(self, request):
        order_id = request.data.get('order_id')
        payment_id = request.data.get('payment_id')
        signature = request.data.get('signature')
        amount = request.data.get('amount')

        try:
            # Verify payment signature
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            razorpay_client.utility.verify_payment_signature(params_dict)
            # Get payment details
            payment_details = razorpay_client.payment.fetch(payment_id)
            # Capture the payment (if not auto-captured)
            razorpay_client.payment.capture(payment_id,int(amount))  # Amount in paise
            response_data = {
                'paymentID': payment_id,
                'orderID': order_id,
                'paymentMethod' : payment_details['method'],
                'paymentDateTime' : datetime.fromtimestamp(payment_details['created_at']).strftime('%Y-%m-%d %H:%M:%S'),
            }
            return Response(response_data,status=status.HTTP_200_OK)
        except razorpay.errors.SignatureVerificationError as e:
            return Response({'error': 'Signature verification failed'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
# Event ViewSet
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.filter(eventActive=True)
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    from rest_framework.views import Response
from rest_framework import status

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.filter(eventActive=True)
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        print("FILES: ", request.FILES)
        print("DATA: ", request.data)
        event_data = {key: value for key, value in request.data.items() if key != 'images'}
        serializer = self.get_serializer(data=event_data, partial=True)
        if serializer.is_valid():
            event_instance = serializer.save()

            # Handle file uploads (images)
            if 'images' in request.FILES:
                for img in request.FILES.getlist('images'):
                    EventImage.objects.create(event=event_instance, images=img)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            event = self.get_object()
        except Event.DoesNotExist:
            return Response({'detail': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        event_data = {key: value for key, value in request.data.items() if key != 'images'}
        serializer = self.get_serializer(event, data=event_data, partial=True)

        if serializer.is_valid():
            event_instance = serializer.save()

            # Update images if provided
            if 'images' in request.FILES:
                # Clear existing images
                event.images.all().delete()

                # Add new images
                for img in request.FILES.getlist('images'):
                    EventImage.objects.create(event=event_instance, images=img)

            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

# Monitoring ViewSet
class MonitoringViewSet(viewsets.ModelViewSet):
    queryset = Monitoring.objects.all()
    serializer_class = MonitoringSerializer
    permission_classes = [IsAuthenticated]

class QrEntryExit(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("hekko")
        data = json.loads(request.body.decode('utf-8')) 
        data = json.loads(data.get("data"))
        print(data,"aaa")
        payment_id = data.get("payment_id")
        print(payment_id)
        event_id = data.get("event_id")
        scan_type = data.get("scan_type")  # "entry" or "exit"

        if not payment_id or not event_id or not scan_type:
            return Response({"error": "Missing required fields."}, status=400)

        # Validate Booking
        booking = get_object_or_404(Booking, paymentID=payment_id, eventID=event_id)

        # Get or Create Monitoring Record
        monitoring, created = Monitoring.objects.get_or_create(bookingID=booking, defaults={
            "entryTime": datetime.now(),
            "exitTime": None,
            "qrCode": "",
            "entryCount": 0,
            "exitCount": 0,
        })

        if scan_type == "entry":
            # Entry Logic
            if monitoring.entryCount >= booking.totalCount:
                return Response({"error": "Entry limit exceeded."}, status=400)

            monitoring.entryCount += 1
            monitoring.entryTime = monitoring.entryTime or data.get("timestamp")
            monitoring.save()
            return Response({"message": "Entry recorded successfully.", "entryCount": monitoring.entryCount})

        elif scan_type == "exit":
            # Exit Logic
            if monitoring.exitCount >= monitoring.entryCount:
                return Response({"error": "Exit count exceeds entry count."}, status=400)

            monitoring.exitCount += 1
            monitoring.exitTime = data.get("timestamp")
            monitoring.save()
            return Response({"message": "Exit recorded successfully.", "exitCount": monitoring.exitCount})

        return Response({"error": "Invalid scan type."}, status=400)
