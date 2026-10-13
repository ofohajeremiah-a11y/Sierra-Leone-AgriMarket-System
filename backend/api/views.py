import csv
import io
import json
from datetime import datetime

from django.contrib.auth import authenticate, get_user_model
from django.http import HttpResponse
from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import *
from .serializers import *
from .services import *


User = get_user_model()


def _obj(model, pk):
    return model.objects.filter(id=pk).first()


@api_view(['POST'])
def register(request):
    phone = str(request.data.get('phone_number', '')).strip()
    username = request.data.get('username') or phone
    password = request.data.get('password', '')

    if not phone or not password:
        return Response(
            {'error': 'phone_number and password are required'},
            status=400
        )

    if User.objects.filter(phone_number=phone).exists():
        return Response(
            {'error': 'Phone number is already registered'},
            status=400
        )

    role = request.data.get('role', 'farmer')

    if role not in dict(User.ROLE_CHOICES):
        role = 'farmer'

    lang = request.data.get('language', 'en')

    user = User.objects.create_user(
        username=username,
        password=password,
        phone_number=phone,
        role=role,
        language=lang
    )

    return Response(UserSerializer(user).data, status=201)


@api_view(['POST'])
def login(request):
    identifier = (
        request.data.get('username')
        or request.data.get('phone_number')
    )

    password = request.data.get('password', '')

    user = (
        User.objects.filter(phone_number=identifier).first()
        if identifier
        else None
    )

    user = (
        authenticate(username=user.username, password=password)
        if user
        else authenticate(username=identifier, password=password)
    )

    if not user:
        return Response(
            {'error': 'Invalid login details'},
            status=401
        )

    return Response({
        'message': 'Login successful',
        'user': UserSerializer(user).data
    })


@api_view(['GET'])
def overview(request):
    user_id = request.GET.get('user')

    alert_query = Alert.objects.filter(is_read=False)

    if user_id:
        alert_query = alert_query.filter(user_id=user_id)

    return Response({
        'users': User.objects.count(),
        'markets': Market.objects.filter(active=True).count(),
        'commodities': Commodity.objects.filter(active=True).count(),
        'price_records': PriceRecord.objects.count(),
        'forecasts': Forecast.objects.count(),
        'recommendations': Recommendation.objects.count(),
        'alerts': alert_query.count(),
        'routes': TransportRoute.objects.filter(active=True).count(),
        'climate_records': ClimateRecord.objects.count(),
        'macro_records': MacroIndicator.objects.count()
    })


@api_view(['GET'])
def markets(request):
    queryset = Market.objects.filter(active=True)

    return Response(
        MarketSerializer(queryset, many=True).data
    )


@api_view(['GET'])
def commodities(request):
    queryset = Commodity.objects.filter(active=True)

    return Response(
        CommoditySerializer(queryset, many=True).data
    )


@api_view(['GET'])
def prices(request):
    queryset = PriceRecord.objects.select_related(
        'market',
        'commodity'
    ).all()

    if request.GET.get('market'):
        queryset = queryset.filter(
            market_id=request.GET['market']
        )

    if request.GET.get('commodity'):
        queryset = queryset.filter(
            commodity_id=request.GET['commodity']
        )

    return Response(
        PriceRecordSerializer(queryset[:500], many=True).data
    )


@api_view(['POST'])
def submit_price(request):
    try:
        market = Market.objects.get(
            id=request.data['market']
        )

        commodity = Commodity.objects.get(
            id=request.data['commodity']
        )

        price = validate_price(
            request.data.get('price')
        )

        previous = PriceRecord.objects.filter(
            market=market,
            commodity=commodity
        ).order_by('-recorded_at').first()

        user = User.objects.filter(
            id=request.data.get('submitted_by')
        ).first()

        if request.data.get('recorded_at'):
            recorded_at = datetime.fromisoformat(
                request.data.get('recorded_at')
            )
        else:
            recorded_at = timezone.now()

        if timezone.is_naive(recorded_at):
            recorded_at = timezone.make_aware(recorded_at)

        price_record = PriceRecord.objects.create(
            market=market,
            commodity=commodity,
            price=price,
            volume=request.data.get('volume', 0),
            recorded_at=recorded_at,
            source=request.data.get('source', 'manual'),
            source_reference=request.data.get(
                'source_reference',
                ''
            ),
            submitted_by=user,
            validated=False
        )

        alerts_created = create_price_alert(
            price_record,
            previous
        )

        return Response({
            'price': PriceRecordSerializer(price_record).data,
            'alerts_created': len(alerts_created),
            'message': (
                'Price submitted. It is awaiting validation.'
            )
        }, status=201)

    except Exception as error:
        return Response(
            {'error': str(error)},
            status=400
        )


@api_view(['POST'])
def validate_prices(request):
    ids = request.data.get('ids', [])
    validated = request.data.get('validated', True)

    note = request.data.get(
        'note',
        'Validated by administrator'
    )

    count = PriceRecord.objects.filter(
        id__in=ids
    ).update(
        validated=validated,
        validation_note=note
    )

    return Response({
        'updated': count
    })


@api_view(['POST'])
def import_prices(request):
    csv_text = request.data.get('csv_text', '')

    if not csv_text:
        return Response(
            {'error': 'csv_text is required'},
            status=400
        )

    created = []
    errors = []

    reader = csv.DictReader(
        io.StringIO(csv_text)
    )

    for row_number, row in enumerate(reader, start=2):
        try:
            market = Market.objects.get(
                name__iexact=row['market'].strip()
            )

            commodity = Commodity.objects.get(
                name__iexact=row['commodity'].strip()
            )

            price = validate_price(
                row['price']
            )

            recorded_at = datetime.fromisoformat(
                row['date']
            )

            if timezone.is_naive(recorded_at):
                recorded_at = timezone.make_aware(
                    recorded_at
                )

            price_record = PriceRecord.objects.create(
                market=market,
                commodity=commodity,
                price=price,
                recorded_at=recorded_at,
                volume=row.get('volume') or 0,
                source=row.get('source') or 'csv_import',
                validated=False
            )

            created.append(price_record)

        except Exception as error:
            errors.append({
                'row': row_number,
                'error': str(error)
            })

    return Response({
        'imported': len(created),
        'errors': errors
    })


@api_view(['GET', 'POST'])
def forecasts(request):
    if request.method == 'POST':
        try:
            market = Market.objects.get(
                id=request.data['market']
            )

            commodity = Commodity.objects.get(
                id=request.data['commodity']
            )

            weeks = max(
                1,
                min(
                    12,
                    int(
                        request.data.get(
                            'weeks',
                            request.data.get(
                                'horizon_weeks',
                                1
                            )
                        )
                    )
                )
            )

            result = forecast_prices(
                market,
                commodity,
                weeks * 7,
                True
            )

            return Response({
                'best_model': result['best_model'],
                'forecasts': ForecastSerializer(
                    result['forecasts'],
                    many=True
                ).data,
                'scores': result['scores']
            })

        except Exception as error:
            return Response(
                {'error': str(error)},
                status=400
            )

    queryset = Forecast.objects.select_related(
        'market',
        'commodity'
    ).order_by('-forecast_date')

    if request.GET.get('market'):
        queryset = queryset.filter(
            market_id=request.GET['market']
        )

    if request.GET.get('commodity'):
        queryset = queryset.filter(
            commodity_id=request.GET['commodity']
        )

    return Response(
        ForecastSerializer(
            queryset[:500],
            many=True
        ).data
    )


@api_view(['GET'])
def model_scores(request):
    queryset = ForecastModelScore.objects.all()

    if request.GET.get('market'):
        queryset = queryset.filter(
            market_id=request.GET['market']
        )

    if request.GET.get('commodity'):
        queryset = queryset.filter(
            commodity_id=request.GET['commodity']
        )

    return Response(
        ScoreSerializer(
            queryset[:100],
            many=True
        ).data
    )


@api_view(['POST'])
def recommendations(request):
    try:
        commodity = Commodity.objects.get(
            id=request.data.get('commodity')
        )

        quantity = float(
            request.data.get('quantity', 100)
        )

        recommendations_list = []

        active_markets = list(
            Market.objects.filter(active=True)
        )

        latest_prices = {}

        for market in active_markets:
            price_record = PriceRecord.objects.filter(
                market=market,
                commodity=commodity
            ).order_by('-recorded_at').first()

            forecast = Forecast.objects.filter(
                market=market,
                commodity=commodity
            ).order_by('-forecast_date').first()

            if forecast or price_record:
                latest_prices[market.id] = float(
                    forecast.predicted_price
                    if forecast
                    else price_record.price
                )
            else:
                latest_prices[market.id] = None

        for origin in active_markets:
            for destination in active_markets:

                if origin.id == destination.id:
                    continue

                if latest_prices.get(origin.id) is None:
                    continue

                if latest_prices.get(destination.id) is None:
                    continue

                route = TransportRoute.objects.filter(
                    origin=origin,
                    destination=destination,
                    active=True
                ).first()

                cost = route_cost(route) if route else 15

                margin = (
                    latest_prices[destination.id]
                    - latest_prices[origin.id]
                    - cost
                )

                if margin > 0:
                    recommendation = Recommendation.objects.create(
                        commodity=commodity,
                        origin=origin,
                        destination=destination,
                        quantity=quantity,
                        expected_margin=round(margin, 2),
                        confidence=round(
                            min(
                                0.95,
                                max(
                                    0.5,
                                    0.5
                                    + abs(margin)
                                    / (
                                        latest_prices[destination.id]
                                        + 1
                                    )
                                    * 0.5
                                )
                            ),
                            2
                        ),
                        rationale=(
                            'Expected price spread is '
                            f"Le {latest_prices[destination.id] - latest_prices[origin.id]:.2f}; "
                            f'estimated movement cost is Le {cost:.2f}.'
                        )
                    )

                    recommendations_list.append(
                        recommendation
                    )

        return Response(
            RecommendationSerializer(
                recommendations_list,
                many=True
            ).data
        )

    except Exception as error:
        return Response(
            {'error': str(error)},
            status=400
        )


@api_view(['POST'])
def optimize(request):
    try:
        commodity = Commodity.objects.get(
            id=request.data['commodity']
        )

        user = User.objects.filter(
            id=request.data.get('user')
        ).first()

        scenario = request.data.get(
            'scenario',
            'normal'
        )

        demand_multiplier = float(
            request.data.get(
                'demand_multiplier',
                1
            )
        )

        fuel_price = (
            float(request.data.get('fuel_price'))
            if request.data.get('fuel_price')
            else None
        )

        plan = optimize_distribution(
            commodity,
            user,
            scenario,
            demand_multiplier,
            fuel_price
        )

        routes = [
            {
                'origin': route.origin.name,
                'destination': route.destination.name,
                'quantity': route.quantity,
                'unit_cost': route.unit_cost,
                'total_cost': route.total_cost,
                'blocked': route.blocked
            }
            for route in plan.routes.select_related(
                'origin',
                'destination'
            )
        ]

        return Response({
            'plan': {
                'id': plan.id,
                'scenario': plan.scenario,
                'total_cost': plan.total_cost,
                'unmet_demand': plan.unmet_demand
            },
            'routes': routes
        })

    except Exception as error:
        return Response(
            {'error': str(error)},
            status=400
        )


@api_view(['GET'])
def route_list(request):
    queryset = TransportRoute.objects.select_related(
        'origin',
        'destination'
    )

    return Response(
        RouteSerializer(queryset, many=True).data
    )


@api_view(['GET'])
def climate(request):
    queryset = ClimateRecord.objects.select_related(
        'market'
    )[:200]

    return Response(
        ClimateSerializer(queryset, many=True).data
    )


@api_view(['GET'])
def macro(request):
    queryset = MacroIndicator.objects.all()[:200]

    return Response(
        MacroSerializer(queryset, many=True).data
    )


@api_view(['GET'])
def supply_demand(request):
    queryset = SupplyDemandRecord.objects.select_related(
        'market',
        'commodity'
    )[:200]

    return Response(
        SupplyDemandSerializer(
            queryset,
            many=True
        ).data
    )


@api_view(['GET'])
def alerts(request):
    queryset = Alert.objects.select_related(
        'commodity',
        'market',
        'user'
    ).order_by('-created_at')

    user_id = request.GET.get('user')

    if user_id:
        queryset = queryset.filter(
            user_id=user_id
        )

    if request.GET.get('unread') == '1':
        queryset = queryset.filter(
            is_read=False
        )

    if request.GET.get('severity'):
        queryset = queryset.filter(
            severity=request.GET['severity']
        )

    return Response(
        AlertSerializer(
            queryset[:200],
            many=True
        ).data
    )


@api_view(['POST'])
def mark_alert_read(request, alert_id):
    alert = Alert.objects.filter(
        id=alert_id
    ).first()

    if not alert:
        return Response(
            {'error': 'Alert not found'},
            status=404
        )

    alert.is_read = True
    alert.sent = True

    alert.save(
        update_fields=['is_read', 'sent']
    )

    return Response(
        AlertSerializer(alert).data
    )


@api_view(['POST'])
def mark_all_alerts_read(request):
    user_id = request.data.get('user')

    if user_id:
        queryset = Alert.objects.filter(
            user_id=user_id
        )
    else:
        queryset = Alert.objects.all()

    count = queryset.filter(
        is_read=False
    ).update(
        is_read=True,
        sent=True
    )

    return Response({
        'marked_read': count
    })


@api_view(['GET', 'POST'])
def subscriptions(request):
    if request.method == 'POST':
        subscription, created = (
            AlertSubscription.objects.update_or_create(
                user_id=request.data['user'],
                commodity_id=(
                    request.data.get('commodity') or None
                ),
                market_id=(
                    request.data.get('market') or None
                ),
                channel=request.data.get(
                    'channel',
                    'dashboard'
                ),
                defaults={
                    'active': request.data.get(
                        'active',
                        True
                    )
                }
            )
        )

        return Response(
            SubscriptionSerializer(subscription).data,
            status=201 if created else 200
        )

    queryset = AlertSubscription.objects.all()

    if request.GET.get('user'):
        queryset = queryset.filter(
            user_id=request.GET['user']
        )

    return Response(
        SubscriptionSerializer(
            queryset,
            many=True
        ).data
    )


# ============================================================
# REPORT EXPORT
# Supports CSV and PDF downloads.
# Supports both ?export=csv and ?format=csv.
# Optional filters: ?commodity=ID and ?market=ID.
# ============================================================

@api_view(['GET'])
def report(request):
    commodity = _obj(
        Commodity,
        request.GET.get('commodity')
    )

    market = _obj(
        Market,
        request.GET.get('market')
    )

    export_format = request.GET.get(
        'export',
        request.GET.get('format', 'csv')
    ).strip().lower()

    if export_format not in ('csv', 'pdf'):
        return Response(
            {
                'error': (
                    'Unsupported export format. '
                    'Use export=csv or export=pdf.'
                )
            },
            status=400
        )

    queryset = PriceRecord.objects.select_related(
        'market',
        'commodity'
    ).order_by('-recorded_at')

    if commodity:
        queryset = queryset.filter(
            commodity_id=commodity.id
        )

    if market:
        queryset = queryset.filter(
            market_id=market.id
        )

    rows = list(queryset[:1000])

    if export_format == 'pdf':
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Table,
            TableStyle,
            Spacer
        )

        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet

        buffer = io.BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4
        )

        styles = getSampleStyleSheet()

        elements = [
            Paragraph(
                'Sierra Leone AgriMarket Intelligence Report',
                styles['Title']
            ),
            Paragraph(
                f'Generated: {timezone.now():%Y-%m-%d %H:%M}',
                styles['Normal']
            ),
            Spacer(1, 12)
        ]

        if commodity:
            elements.append(
                Paragraph(
                    f'Commodity: {commodity.name}',
                    styles['Normal']
                )
            )

        if market:
            elements.append(
                Paragraph(
                    f'Market: {market.name}',
                    styles['Normal']
                )
            )

        elements.append(Spacer(1, 8))

        data = [
            [
                'Date',
                'Market',
                'Commodity',
                'Price',
                'Validated'
            ]
        ]

        for record in rows[:60]:
            data.append([
                str(record.recorded_at.date()),
                record.market.name,
                record.commodity.name,
                f'Le {record.price:.2f}',
                str(record.validated)
            ])

        table = Table(
            data,
            repeatRows=1
        )

        table.setStyle(
            TableStyle([
                (
                    'BACKGROUND',
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    'GRID',
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.grey
                ),
                (
                    'FONTSIZE',
                    (0, 0),
                    (-1, -1),
                    7
                ),
                (
                    'VALIGN',
                    (0, 0),
                    (-1, -1),
                    'TOP'
                )
            ])
        )

        elements.append(table)

        document.build(elements)

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/pdf'
        )

        response['Content-Disposition'] = (
            'attachment; filename="agrimarket_report.pdf"'
        )

        return response

    # CSV export
    buffer = io.StringIO()

    writer = csv.writer(buffer)

    writer.writerow([
        'Date',
        'Market',
        'Commodity',
        'Price',
        'Unit',
        'Validated'
    ])

    for record in rows:
        writer.writerow([
            record.recorded_at.date(),
            record.market.name,
            record.commodity.name,
            record.price,
            record.commodity.unit,
            record.validated
        ])

    response = HttpResponse(
        buffer.getvalue(),
        content_type='text/csv; charset=utf-8'
    )

    response['Content-Disposition'] = (
        'attachment; filename="agrimarket_report.csv"'
    )

    return response


@api_view(['POST'])
def ussd(request):
    ussd_text = (
        request.data.get('text') or ''
    ).strip()

    parts = (
        ussd_text.split('*')
        if ussd_text
        else []
    )

    if not parts:
        return Response({
            'response': (
                'CON AgriMarket\n'
                '1. Check Price\n'
                '2. Forecast\n'
                '3. Report Price\n'
                '4. Subscribe SMS\n'
                '5. Help'
            )
        })

    menus = {
        '1': (
            'price',
            'Select commodity\n'
            '1. Rice\n'
            '2. Cassava\n'
            '3. Maize\n'
            '4. Groundnuts\n'
            '5. Palm Oil'
        ),
        '2': (
            'forecast',
            'Select commodity\n'
            '1. Rice\n'
            '2. Cassava\n'
            '3. Maize\n'
            '4. Groundnuts\n'
            '5. Palm Oil'
        )
    }

    if parts[0] in menus and len(parts) == 1:
        return Response({
            'response': 'CON ' + menus[parts[0]][1]
        })

    if parts[0] in menus and len(parts) == 2:
        return Response({
            'response': (
                'CON Select market\n'
                '1. Freetown\n'
                '2. Bo\n'
                '3. Makeni\n'
                '4. Kenema\n'
                '5. Port Loko'
            )
        })

    if parts[0] in menus and len(parts) >= 3:
        try:
            commodity_number = int(parts[1])
            market_number = int(parts[2])
        except (ValueError, IndexError):
            return Response({
                'response': (
                    'END Invalid selection. '
                    'Please start again.'
                )
            })

        commodity_name = {
            1: 'Rice',
            2: 'Cassava',
            3: 'Maize',
            4: 'Groundnuts',
            5: 'Palm Oil'
        }.get(commodity_number, '')

        market_name = {
            1: 'Freetown',
            2: 'Bo',
            3: 'Makeni',
            4: 'Kenema',
            5: 'Port Loko'
        }.get(market_number, '')

        if not commodity_name or not market_name:
            return Response({
                'response': (
                    'END Invalid commodity or market selection.'
                )
            })

        commodity = Commodity.objects.filter(
            name=commodity_name
        ).first()

        market = Market.objects.filter(
            name=market_name
        ).first()

        if not commodity or not market:
            return Response({
                'response': (
                    'END No matching commodity or market '
                    'was found.'
                )
            })

        if parts[0] == '1':
            price_record = PriceRecord.objects.filter(
                commodity=commodity,
                market=market
            ).order_by('-recorded_at').first()

            if price_record:
                message = (
                    f'END {commodity_name} in {market_name}: '
                    f'Le {price_record.price:.2f}/'
                    f'{commodity.unit}'
                )
            else:
                message = (
                    f'END No price data available for '
                    f'{commodity_name} in {market_name}.'
                )

            return Response({
                'response': message
            })

        forecast = Forecast.objects.filter(
            commodity=commodity,
            market=market
        ).order_by('forecast_date').first()

        if forecast:
            message = (
                'END Forecast: '
                f'Le {forecast.predicted_price:.2f}/'
                f'{commodity.unit}'
            )
        else:
            message = 'END No forecast available.'

        return Response({
            'response': message
        })

    if parts[0] == '3':
        return Response({
            'response': (
                'END Price reporting is available '
                'on the web data-entry form.'
            )
        })

    if parts[0] == '4':
        return Response({
            'response': (
                'END SMS subscription is managed '
                'from the dashboard. Send your phone '
                'number through the web profile.'
            )
        })

    if parts[0] == '5':
        return Response({
            'response': (
                'END AgriMarket provides market prices, '
                'forecasts, and agricultural market '
                'information for Sierra Leone.'
            )
        })

    return Response({
        'response': (
            'END Use 1 for prices, 2 for forecasts, '
            '3 to report a price, 4 for SMS subscriptions, '
            'or 5 for help.'
        )
    })
