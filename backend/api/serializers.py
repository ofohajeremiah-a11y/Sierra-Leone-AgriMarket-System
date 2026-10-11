from rest_framework import serializers
from .models import *
class UserSerializer(serializers.ModelSerializer):
    role_label=serializers.CharField(source='get_role_display',read_only=True)
    class Meta: model=User; fields=['id','username','phone_number','role','role_label','language','is_active']
class MarketSerializer(serializers.ModelSerializer):
    class Meta: model=Market; fields='__all__'
class CommoditySerializer(serializers.ModelSerializer):
    class Meta: model=Commodity; fields='__all__'
class PriceRecordSerializer(serializers.ModelSerializer):
    market_name=serializers.CharField(source='market.name',read_only=True); commodity_name=serializers.CharField(source='commodity.name',read_only=True)
    class Meta: model=PriceRecord; fields='__all__'
class ForecastSerializer(serializers.ModelSerializer):
    market_name=serializers.CharField(source='market.name',read_only=True); commodity_name=serializers.CharField(source='commodity.name',read_only=True)
    class Meta: model=Forecast; fields='__all__'
class ScoreSerializer(serializers.ModelSerializer):
    class Meta: model=ForecastModelScore; fields='__all__'
class RecommendationSerializer(serializers.ModelSerializer):
    origin_name=serializers.CharField(source='origin.name',read_only=True); destination_name=serializers.CharField(source='destination.name',read_only=True); commodity_name=serializers.CharField(source='commodity.name',read_only=True)
    class Meta: model=Recommendation; fields='__all__'
class AlertSerializer(serializers.ModelSerializer):
    commodity_name=serializers.CharField(source='commodity.name',read_only=True); market_name=serializers.CharField(source='market.name',read_only=True); severity_label=serializers.CharField(source='get_severity_display',read_only=True)
    class Meta: model=Alert; fields='__all__'
class ClimateSerializer(serializers.ModelSerializer):
    market_name=serializers.CharField(source='market.name',read_only=True)
    class Meta: model=ClimateRecord; fields='__all__'
class MacroSerializer(serializers.ModelSerializer):
    class Meta: model=MacroIndicator; fields='__all__'
class SupplyDemandSerializer(serializers.ModelSerializer):
    market_name=serializers.CharField(source='market.name',read_only=True); commodity_name=serializers.CharField(source='commodity.name',read_only=True)
    class Meta: model=SupplyDemandRecord; fields='__all__'
class RouteSerializer(serializers.ModelSerializer):
    origin_name=serializers.CharField(source='origin.name',read_only=True); destination_name=serializers.CharField(source='destination.name',read_only=True)
    class Meta: model=TransportRoute; fields='__all__'
class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta: model=AlertSubscription; fields='__all__'
