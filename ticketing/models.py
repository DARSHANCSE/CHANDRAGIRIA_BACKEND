from django.db import models

class Event(models.Model):
    id = models.AutoField(primary_key=True)
    eventName = models.CharField(max_length=250)
    eventTiming = models.TimeField()
    eventCapacity = models.IntegerField()
    eventPriceAdult = models.FloatField()
    eventPriceChild = models.FloatField()
    eventStatus = models.BooleanField()
    eventDisplay = models.BooleanField()
    eventActive = models.BooleanField()
    # eventimages = models.ImageField(upload_to='Event_images',null=True, blank=True)  
class EventImage(models.Model):
    event = models.ForeignKey(Event, related_name='images', on_delete=models.CASCADE)
    images = models.ImageField(upload_to='Event_images', null=True, blank=True)

class Booking(models.Model):
    id = models.AutoField(primary_key=True)
    eventID = models.ForeignKey(Event, on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    email = models.EmailField(max_length=250)
    phone = models.CharField(max_length=20)
    date = models.DateTimeField()
    adultsCount = models.IntegerField()
    childrenCount = models.IntegerField()
    totalCount = models.IntegerField()
    paymentID = models.CharField(max_length=250,unique=True)
    paymentMethod = models.CharField(max_length=250)
    entryTime = models.DateTimeField(null=True)
    exitTime = models.DateTimeField(null=True)

class Monitoring(models.Model):
    id = models.AutoField(primary_key=True)
    bookingID = models.ForeignKey(Booking, on_delete=models.CASCADE)
    entryTime = models.DateTimeField(null=True)
    exitTime = models.DateTimeField(null=True)
    qrCode = models.CharField(max_length=250)
    entryCount = models.IntegerField(default=0,null=False)
    exitCount = models.IntegerField(default=0,null=False)