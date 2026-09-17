from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),
        ('trader', 'Trader'),
        ('enumerator', 'Enumerator'),
        ('policymaker', 'Policymaker'),
        ('admin', 'Administrator'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='farmer')
    phone_number = models.CharField(max_length=30, unique=True, null=True, blank=True)


class Market(models.Model):
    name = models.CharField(max_length=100, unique=True)
    district = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Commodity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=30, default='kg')
    storable = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PriceRecord(models.Model):
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='prices')
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE, related_name='prices')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    volume = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    recorded_at = models.DateTimeField()
    source = models.CharField(max_length=100, default='manual')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']
        indexes = [models.Index(fields=['market', 'commodity', 'recorded_at'])]


class Forecast(models.Model):
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE)
    forecast_date = models.DateField()
    predicted_price = models.DecimalField(max_digits=12, decimal_places=2)
    lower_bound = models.DecimalField(max_digits=12, decimal_places=2)
    upper_bound = models.DecimalField(max_digits=12, decimal_places=2)
    model_name = models.CharField(max_length=50, default='ARIMA')
    rmse = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['forecast_date']


class Recommendation(models.Model):
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE)
    origin = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='recommendation_origins')
    destination = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='recommendation_destinations')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    action = models.CharField(max_length=30, default='transport')
    expected_margin = models.DecimalField(max_digits=12, decimal_places=2)
    confidence = models.DecimalField(max_digits=5, decimal_places=2)
    rationale = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Alert(models.Model):
    SEVERITY_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    TYPE_CHOICES = [
        ('price_change', 'Price Change'),
        ('price_submission', 'New Price'),
        ('forecast_change', 'Forecast Change'),
        ('opportunity', 'Market Opportunity'),
        ('system', 'System'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE, null=True, blank=True)
    market = models.ForeignKey(Market, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=160, default='Market Alert')
    message = models.CharField(max_length=255)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='info')
    alert_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='system')
    previous_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    percent_change = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    sent = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'is_read', 'created_at'])]
