from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from .models import Event, Booking, Monitoring
from .serializers import EventSerializer, BookingSerializer, MonitoringSerializer
from .utils import createRazorpayClient
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import ModifiedTokenObtainPairSerializer,CustomTokenRefreshSerializer
from datetime import datetime
import secrets
import razorpay





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
            # print("aaaa") #,request.data["access"])
            access_tok = request.data.get("access")
            print(access_tok)
            token = RefreshToken(access_tok).access_token
            token.blacklist()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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

    def put(self, request, *args, **kwargs):
        instance = self.get_object()  
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)
# Booking ViewSet
class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

# Monitoring ViewSet
class MonitoringViewSet(viewsets.ModelViewSet):
    queryset = Monitoring.objects.all()
    serializer_class = MonitoringSerializer
    permission_classes = [IsAuthenticated]
