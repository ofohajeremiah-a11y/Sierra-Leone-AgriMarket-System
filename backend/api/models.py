from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES=[('farmer','Farmer'),('trader','Trader'),('transporter','Transporter'),('field_agent','Field Agent'),('policymaker','Policy Maker'),('analyst','Analyst'),('admin','Administrator')]
    LANGUAGE_CHOICES=[('en','English'),('kr','Krio')]
    role=models.CharField(max_length=20,choices=ROLE_CHOICES,default='farmer')
    phone_number=models.CharField(max_length=30,unique=True,null=True,blank=True)
    language=models.CharField(max_length=2,choices=LANGUAGE_CHOICES,default='en')

class Market(models.Model):
    name=models.CharField(max_length=100,unique=True); district=models.CharField(max_length=100); region=models.CharField(max_length=80,default='Southern')
    latitude=models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True); longitude=models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True)
    supply_capacity=models.DecimalField(max_digits=12,decimal_places=2,default=1000); demand_baseline=models.DecimalField(max_digits=12,decimal_places=2,default=800)
    road_condition=models.CharField(max_length=20,default='normal'); active=models.BooleanField(default=True)
    def __str__(self): return self.name

class Commodity(models.Model):
    name=models.CharField(max_length=100,unique=True); unit=models.CharField(max_length=30,default='kg'); storable=models.BooleanField(default=True); active=models.BooleanField(default=True)
    def __str__(self): return self.name

class PriceRecord(models.Model):
    market=models.ForeignKey(Market,on_delete=models.CASCADE,related_name='prices'); commodity=models.ForeignKey(Commodity,on_delete=models.CASCADE,related_name='prices')
    price=models.DecimalField(max_digits=12,decimal_places=2); volume=models.DecimalField(max_digits=12,decimal_places=2,default=0); recorded_at=models.DateTimeField()
    source=models.CharField(max_length=100,default='manual'); source_reference=models.CharField(max_length=255,blank=True); submitted_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    validated=models.BooleanField(default=False); validation_note=models.CharField(max_length=255,blank=True); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-recorded_at']; indexes=[models.Index(fields=['market','commodity','recorded_at'])]

class ClimateRecord(models.Model):
    market=models.ForeignKey(Market,on_delete=models.CASCADE,related_name='climate'); date=models.DateField(); rainfall_mm=models.FloatField(default=0); temperature_c=models.FloatField(default=27); source=models.CharField(max_length=100,default='demo')
    class Meta: unique_together=('market','date'); ordering=['-date']

class MacroIndicator(models.Model):
    date=models.DateField(unique=True); exchange_rate_sle_usd=models.FloatField(default=0); cpi=models.FloatField(default=0); inflation_pct=models.FloatField(default=0); fuel_price_sle_litre=models.FloatField(default=0); source=models.CharField(max_length=100,default='demo')
    class Meta: ordering=['-date']

class SupplyDemandRecord(models.Model):
    market=models.ForeignKey(Market,on_delete=models.CASCADE,related_name='supply_demand'); commodity=models.ForeignKey(Commodity,on_delete=models.CASCADE); date=models.DateField(); supply_qty=models.FloatField(default=0); demand_qty=models.FloatField(default=0); source=models.CharField(max_length=100,default='demo')
    class Meta: unique_together=('market','commodity','date'); ordering=['-date']

class TransportRoute(models.Model):
    origin=models.ForeignKey(Market,on_delete=models.CASCADE,related_name='routes_from'); destination=models.ForeignKey(Market,on_delete=models.CASCADE,related_name='routes_to')
    distance_km=models.FloatField(default=0); base_cost_per_km=models.FloatField(default=1); fuel_litre_per_km=models.FloatField(default=.15); spoilage_pct=models.FloatField(default=2); blocked=models.BooleanField(default=False); active=models.BooleanField(default=True)
    class Meta: unique_together=('origin','destination')

class Forecast(models.Model):
    market=models.ForeignKey(Market,on_delete=models.CASCADE); commodity=models.ForeignKey(Commodity,on_delete=models.CASCADE); forecast_date=models.DateField(); predicted_price=models.DecimalField(max_digits=12,decimal_places=2); lower_bound=models.DecimalField(max_digits=12,decimal_places=2); upper_bound=models.DecimalField(max_digits=12,decimal_places=2)
    model_name=models.CharField(max_length=60,default='SARIMA'); rmse=models.DecimalField(max_digits=12,decimal_places=4,null=True,blank=True); mae=models.DecimalField(max_digits=12,decimal_places=4,null=True,blank=True); mape=models.DecimalField(max_digits=12,decimal_places=4,null=True,blank=True); horizon_days=models.IntegerField(default=7); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['forecast_date']

class ForecastModelScore(models.Model):
    market=models.ForeignKey(Market,on_delete=models.CASCADE); commodity=models.ForeignKey(Commodity,on_delete=models.CASCADE); model_name=models.CharField(max_length=60); mae=models.FloatField(null=True); rmse=models.FloatField(null=True); mape=models.FloatField(null=True); selected=models.BooleanField(default=False); evaluated_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['rmse']

class ShipmentPlan(models.Model):
    SCENARIOS=[('normal','Normal'),('blocked','Blocked Road'),('demand_shock','Demand Shock')]
    commodity=models.ForeignKey(Commodity,on_delete=models.CASCADE); scenario=models.CharField(max_length=30,choices=SCENARIOS,default='normal'); fuel_price=models.FloatField(default=0); demand_multiplier=models.FloatField(default=1); total_cost=models.FloatField(default=0); unmet_demand=models.FloatField(default=0); created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True)

class ShipmentRoute(models.Model):
    plan=models.ForeignKey(ShipmentPlan,on_delete=models.CASCADE,related_name='routes'); origin=models.ForeignKey(Market,on_delete=models.CASCADE,related_name='shipments_from'); destination=models.ForeignKey(Market,on_delete=models.CASCADE,related_name='shipments_to'); quantity=models.FloatField(default=0); unit_cost=models.FloatField(default=0); total_cost=models.FloatField(default=0); blocked=models.BooleanField(default=False)

class Recommendation(models.Model):
    commodity=models.ForeignKey(Commodity,on_delete=models.CASCADE); origin=models.ForeignKey(Market,on_delete=models.CASCADE,related_name='recommendation_origins'); destination=models.ForeignKey(Market,on_delete=models.CASCADE,related_name='recommendation_destinations'); quantity=models.DecimalField(max_digits=12,decimal_places=2); action=models.CharField(max_length=30,default='transport'); expected_margin=models.DecimalField(max_digits=12,decimal_places=2); confidence=models.DecimalField(max_digits=5,decimal_places=2); rationale=models.TextField(); created_at=models.DateTimeField(auto_now_add=True)

class Alert(models.Model):
    SEVERITY_CHOICES=[('info','Information'),('warning','Warning'),('critical','Critical')]; TYPE_CHOICES=[('price_change','Price Change'),('price_submission','New Price'),('forecast_change','Forecast Change'),('opportunity','Market Opportunity'),('system','System'),('low_price','Low Price')]
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='alerts'); commodity=models.ForeignKey(Commodity,on_delete=models.CASCADE,null=True,blank=True); market=models.ForeignKey(Market,on_delete=models.CASCADE,null=True,blank=True); title=models.CharField(max_length=160,default='Market Alert'); message=models.CharField(max_length=255); severity=models.CharField(max_length=10,choices=SEVERITY_CHOICES,default='info'); alert_type=models.CharField(max_length=30,choices=TYPE_CHOICES,default='system'); previous_price=models.DecimalField(max_digits=12,decimal_places=2,null=True,blank=True); current_price=models.DecimalField(max_digits=12,decimal_places=2,null=True,blank=True); percent_change=models.DecimalField(max_digits=8,decimal_places=2,null=True,blank=True); channel=models.CharField(max_length=10,default='dashboard'); sent=models.BooleanField(default=False); is_read=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']; indexes=[models.Index(fields=['user','is_read','created_at'])]

class AlertSubscription(models.Model):
    CHANNELS=[('dashboard','Dashboard'),('sms','SMS'),('ussd','USSD')]
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='subscriptions'); commodity=models.ForeignKey(Commodity,on_delete=models.CASCADE,null=True,blank=True); market=models.ForeignKey(Market,on_delete=models.CASCADE,null=True,blank=True); channel=models.CharField(max_length=10,choices=CHANNELS,default='dashboard'); active=models.BooleanField(default=True); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: unique_together=('user','commodity','market','channel')
