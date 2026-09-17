from django.contrib import admin
from .models import User, Market, Commodity, PriceRecord, Forecast, Recommendation, Alert


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'phone_number', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'phone_number')


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'alert_type', 'user', 'commodity', 'market', 'is_read', 'created_at')
    list_filter = ('severity', 'alert_type', 'is_read', 'sent')
    search_fields = ('title', 'message', 'user__username', 'commodity__name', 'market__name')


admin.site.register(Market)
admin.site.register(Commodity)
admin.site.register(PriceRecord)
admin.site.register(Forecast)
admin.site.register(Recommendation)
