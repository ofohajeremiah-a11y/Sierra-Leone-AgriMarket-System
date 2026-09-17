from datetime import datetime
from django.contrib.auth import authenticate, get_user_model
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import *
from .serializers import *
from .services import validate_price, forecast_prices, make_recommendations, create_price_alert

User = get_user_model()


@api_view(['POST'])
def register(request):
    phone = request.data.get('phone_number', '').strip()
    username = request.data.get('username', phone)
    password = request.data.get('password', '')
    if not phone or not password:
        return Response({'error': 'phone_number and password are required'}, status=400)
    if User.objects.filter(phone_number=phone).exists():
        return Response({'error': 'Phone number is already registered'}, status=400)
    role = request.data.get('role', 'farmer')
    if role not in dict(User.ROLE_CHOICES):
        role = 'farmer'
    u = User.objects.create_user(username=username, password=password, phone_number=phone, role=role)
    return Response(UserSerializer(u).data, status=201)


@api_view(['POST'])
def login(request):
    identifier = request.data.get('username') or request.data.get('phone_number')
    password = request.data.get('password', '')
    u = User.objects.filter(phone_number=identifier).first() if identifier else None
    if u:
        u = authenticate(username=u.username, password=password)
    else:
        u = authenticate(username=identifier, password=password)
    if not u:
        return Response({'error': 'Invalid login details'}, status=401)
    return Response({'message': 'Login successful', 'user': UserSerializer(u).data})


@api_view(['GET'])
def overview(request):
    user_id = request.GET.get('user')
    alert_qs = Alert.objects.filter(is_read=False)
    if user_id:
        alert_qs = alert_qs.filter(user_id=user_id)
    return Response({
        'users': User.objects.count(),
        'markets': Market.objects.filter(active=True).count(),
        'commodities': Commodity.objects.filter(active=True).count(),
        'price_records': PriceRecord.objects.count(),
        'forecasts': Forecast.objects.count(),
        'recommendations': Recommendation.objects.count(),
        'alerts': alert_qs.count(),
    })


@api_view(['GET'])
def markets(request):
    return Response(MarketSerializer(Market.objects.filter(active=True), many=True).data)


@api_view(['GET'])
def commodities(request):
    return Response(CommoditySerializer(Commodity.objects.filter(active=True), many=True).data)


@api_view(['GET'])
def prices(request):
    qs = PriceRecord.objects.select_related('market', 'commodity').all()
    if request.GET.get('market'):
        qs = qs.filter(market_id=request.GET['market'])
    if request.GET.get('commodity'):
        qs = qs.filter(commodity_id=request.GET['commodity'])
    return Response(PriceRecordSerializer(qs[:200], many=True).data)


@api_view(['POST'])
def submit_price(request):
    try:
        price = validate_price(request.data.get('price'))
        market = Market.objects.get(id=request.data['market'])
        commodity = Commodity.objects.get(id=request.data['commodity'])
        previous = PriceRecord.objects.filter(market=market, commodity=commodity).order_by('-recorded_at').first()
        submitted_by = User.objects.filter(id=request.data.get('submitted_by')).first() if request.data.get('submitted_by') else None
        recorded_at = datetime.fromisoformat(request.data.get('recorded_at')) if request.data.get('recorded_at') else timezone.now()
        if timezone.is_naive(recorded_at):
            recorded_at = timezone.make_aware(recorded_at)
        obj = PriceRecord.objects.create(
            market=market, commodity=commodity, price=price,
            volume=request.data.get('volume', 0), recorded_at=recorded_at,
            source=request.data.get('source', 'manual'), submitted_by=submitted_by, validated=False
        )
        alerts_created = create_price_alert(obj, previous)
        return Response({
            'price': PriceRecordSerializer(obj).data,
            'alerts_created': len(alerts_created),
            'message': 'Price submitted and the alert engine has checked the change.'
        }, status=201)
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['GET', 'POST'])
def forecasts(request):
    if request.method == 'POST':
        try:
            m = Market.objects.get(id=request.data['market'])
            c = Commodity.objects.get(id=request.data['commodity'])
            fs = forecast_prices(m, c, int(request.data.get('horizon', 7)))
            return Response(ForecastSerializer(fs, many=True).data)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    qs = Forecast.objects.select_related('market', 'commodity').order_by('-forecast_date')
    if request.GET.get('market'):
        qs = qs.filter(market_id=request.GET['market'])
    if request.GET.get('commodity'):
        qs = qs.filter(commodity_id=request.GET['commodity'])
    return Response(ForecastSerializer(qs[:100], many=True).data)


@api_view(['POST'])
def recommendations(request):
    try:
        c = Commodity.objects.get(id=request.data['commodity'])
        recs = make_recommendations(c, float(request.data.get('quantity', 100)))
        return Response(RecommendationSerializer(recs, many=True).data)
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['GET'])
def alerts(request):
    qs = Alert.objects.select_related('commodity', 'market', 'user').order_by('-created_at')
    user_id = request.GET.get('user')
    if user_id:
        qs = qs.filter(user_id=user_id)
    if request.GET.get('unread') == '1':
        qs = qs.filter(is_read=False)
    if request.GET.get('severity'):
        qs = qs.filter(severity=request.GET['severity'])
    return Response(AlertSerializer(qs[:100], many=True).data)


@api_view(['POST'])
def mark_alert_read(request, alert_id):
    alert = Alert.objects.filter(id=alert_id).first()
    if not alert:
        return Response({'error': 'Alert not found'}, status=404)
    alert.is_read = True
    alert.sent = True
    alert.save(update_fields=['is_read', 'sent'])
    return Response(AlertSerializer(alert).data)


@api_view(['POST'])
def mark_all_alerts_read(request):
    user_id = request.data.get('user') or request.GET.get('user')
    qs = Alert.objects.filter(user_id=user_id) if user_id else Alert.objects.all()
    count = qs.filter(is_read=False).update(is_read=True, sent=True)
    return Response({'marked_read': count})


@api_view(['GET'])
def report(request):
    commodity = Commodity.objects.filter(id=request.GET.get('commodity')).first() if request.GET.get('commodity') else None
    market = Market.objects.filter(id=request.GET.get('market')).first() if request.GET.get('market') else None
    qs = PriceRecord.objects.select_related('market', 'commodity').order_by('recorded_at')
    if commodity:
        qs = qs.filter(commodity=commodity)
    if market:
        qs = qs.filter(market=market)
    rows = list(qs[:500])
    lines = [
        'Sierra Leone AgriMarket - Market Intelligence Report',
        'Generated: ' + timezone.now().strftime('%Y-%m-%d %H:%M'),
        'Commodity: ' + (commodity.name if commodity else 'All'),
        'Market: ' + (market.name if market else 'All'),
        '', 'Date,Market,Commodity,Price,Unit,Validated'
    ]
    for r in rows:
        lines.append(f'{r.recorded_at.date()},{r.market.name},{r.commodity.name},{r.price},{r.commodity.unit},{r.validated}')
    return HttpResponse('\n'.join(lines), content_type='text/csv', headers={'Content-Disposition': 'attachment; filename="agrimarket_report.csv"'})


@api_view(['POST'])
def ussd(request):
    session = request.data.get('sessionId', 'demo')
    text = (request.data.get('text') or '').strip()
    parts = text.split('*') if text else []
    if not parts:
        return Response({'response': 'CON Welcome to AgriMarket\n1. Check Price\n2. Get Forecast\n3. Report Price\n4. Help', 'sessionId': session})
    if parts[0] == '1':
        if len(parts) == 1:
            return Response({'response': 'CON Select commodity\n1. Rice\n2. Cassava\n3. Groundnuts', 'sessionId': session})
        if len(parts) == 2:
            return Response({'response': 'CON Select market\n1. Freetown\n2. Bo\n3. Makeni', 'sessionId': session})
        c = Commodity.objects.filter(name__iexact={'1': 'Rice', '2': 'Cassava', '3': 'Groundnuts'}.get(parts[1], '')).first()
        m = Market.objects.filter(name__iexact={'1': 'Freetown', '2': 'Bo', '3': 'Makeni'}.get(parts[2], '')).first()
        p = PriceRecord.objects.filter(commodity=c, market=m).order_by('-recorded_at').first() if c and m else None
        return Response({'response': f'END Current {c.name if c else "price"} price in {m.name if m else "market"}: {p.price if p else "No data"} per kg', 'sessionId': session})
    if parts[0] == '2':
        if len(parts) == 1:
            return Response({'response': 'CON Forecast for\n1. Rice\n2. Cassava\n3. Groundnuts', 'sessionId': session})
        if len(parts) == 2:
            return Response({'response': 'CON Select market\n1. Freetown\n2. Bo\n3. Makeni', 'sessionId': session})
        c = Commodity.objects.filter(name__iexact={'1': 'Rice', '2': 'Cassava', '3': 'Groundnuts'}.get(parts[1], '')).first()
        m = Market.objects.filter(name__iexact={'1': 'Freetown', '2': 'Bo', '3': 'Makeni'}.get(parts[2], '')).first()
        f = Forecast.objects.filter(commodity=c, market=m).order_by('forecast_date').first() if c and m else None
        return Response({'response': f'END 7-day forecast: {f.predicted_price:.2f}/kg ({f.lower_bound:.2f}-{f.upper_bound:.2f})' if f else 'END No forecast available.', 'sessionId': session})
    if parts[0] == '3':
        return Response({'response': 'END Price reporting is available through the enumerator/web form.', 'sessionId': session})
    return Response({'response': 'END Use 1 for price, 2 for forecast, 3 to report a price.', 'sessionId': session})
