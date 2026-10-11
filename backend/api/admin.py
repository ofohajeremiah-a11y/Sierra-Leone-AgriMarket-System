from django.contrib import admin
from .models import *
@admin.register(User)
class UserAdmin(admin.ModelAdmin): list_display=('username','phone_number','role','language','is_active','is_staff'); list_filter=('role','language','is_active'); search_fields=('username','phone_number')
@admin.register(PriceRecord)
class PriceAdmin(admin.ModelAdmin): list_display=('recorded_at','market','commodity','price','validated','source'); list_filter=('validated','source','commodity','market'); search_fields=('market__name','commodity__name')
@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin): list_display=('title','severity','channel','user','is_read','created_at'); list_filter=('severity','channel','is_read')
admin.site.register([Market,Commodity,ClimateRecord,MacroIndicator,SupplyDemandRecord,TransportRoute,Forecast,ForecastModelScore,ShipmentPlan,ShipmentRoute,Recommendation,AlertSubscription])
