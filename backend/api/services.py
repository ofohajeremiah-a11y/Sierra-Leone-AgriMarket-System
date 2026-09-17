from datetime import timedelta
from decimal import Decimal
from statistics import pstdev

from django.db import transaction
from django.utils import timezone

from .models import PriceRecord, Forecast, Recommendation, Market, Commodity, Alert, User


# Alert rules used by the pilot system. They can later be moved to an admin settings table.
INFO_CHANGE = Decimal('5')
WARNING_CHANGE = Decimal('10')
CRITICAL_CHANGE = Decimal('20')


def validate_price(value):
    v = Decimal(str(value))
    if v <= 0:
        raise ValueError('Price must be greater than zero.')
    if v > Decimal('100000000'):
        raise ValueError('Price is outside the accepted range.')
    return v


def _severity_for_change(change):
    magnitude = abs(Decimal(str(change)))
    if magnitude >= CRITICAL_CHANGE:
        return 'critical'
    if magnitude >= WARNING_CHANGE:
        return 'warning'
    if magnitude >= INFO_CHANGE:
        return 'info'
    return None


def _recipients(kind='all'):
    users = User.objects.filter(is_active=True)
    if kind == 'market':
        return users.filter(role__in=['farmer', 'trader', 'policymaker', 'admin'])
    if kind == 'data':
        return users.filter(role__in=['enumerator', 'policymaker', 'admin'])
    if kind == 'opportunity':
        return users.filter(role__in=['farmer', 'trader', 'admin'])
    return users


def _create_alerts(title, message, commodity=None, market=None, severity='info', alert_type='system',
                   previous_price=None, current_price=None, percent_change=None, recipient_kind='all'):
    """Create one alert per relevant active user, while avoiding duplicate alerts in the same minute."""
    recipients = _recipients(recipient_kind)
    created = []
    now = timezone.now()
    for user in recipients:
        duplicate = Alert.objects.filter(
            user=user,
            commodity=commodity,
            market=market,
            alert_type=alert_type,
            title=title,
            created_at__gte=now - timedelta(minutes=2),
        ).exists()
        if duplicate:
            continue
        created.append(Alert.objects.create(
            user=user,
            commodity=commodity,
            market=market,
            title=title,
            message=message[:255],
            severity=severity,
            alert_type=alert_type,
            previous_price=previous_price,
            current_price=current_price,
            percent_change=percent_change,
        ))
    return created


def create_price_alert(new_record, previous_record=None):
    """Automatically create an alert when a newly submitted price changes materially."""
    if previous_record is None:
        return _create_alerts(
            title='New market price recorded',
            message=f'{new_record.commodity.name} in {new_record.market.name}: new price {new_record.price:.2f} per {new_record.commodity.unit}.',
            commodity=new_record.commodity,
            market=new_record.market,
            severity='info',
            alert_type='price_submission',
            current_price=new_record.price,
            recipient_kind='data',
        )

    previous = Decimal(previous_record.price)
    current = Decimal(new_record.price)
    if previous <= 0:
        return []
    change = ((current - previous) / previous) * Decimal('100')
    severity = _severity_for_change(change)
    if severity is None:
        return []

    direction = 'increased' if change > 0 else 'decreased'
    symbol = '↑' if change > 0 else '↓'
    title = f'Price {"increase" if change > 0 else "decrease"} alert'
    message = (
        f'{new_record.commodity.name} price in {new_record.market.name} {direction} by '
        f'{abs(change):.1f}% ({previous:.2f} → {current:.2f} per {new_record.commodity.unit}).'
    )
    return _create_alerts(
        title=title,
        message=f'{symbol} {message}',
        commodity=new_record.commodity,
        market=new_record.market,
        severity=severity,
        alert_type='price_change',
        previous_price=previous,
        current_price=current,
        percent_change=change,
        recipient_kind='market',
    )


def create_forecast_alerts(market, commodity, forecasts):
    if not forecasts:
        return []
    latest = PriceRecord.objects.filter(market=market, commodity=commodity).order_by('-recorded_at').first()
    if not latest:
        return []
    avg_pred = Decimal(str(sum(float(f.predicted_price) for f in forecasts) / len(forecasts)))
    current = Decimal(latest.price)
    if current <= 0:
        return []
    change = ((avg_pred - current) / current) * Decimal('100')
    magnitude = abs(change)
    if magnitude < WARNING_CHANGE:
        return []
    severity = 'critical' if magnitude >= CRITICAL_CHANGE else 'warning'
    direction = 'increase' if change > 0 else 'decrease'
    return _create_alerts(
        title=f'Forecast {direction} alert',
        message=(f'{commodity.name} in {market.name} is forecast to {direction} by about '
                 f'{magnitude:.1f}% over the next {len(forecasts)} days (current {current:.2f}, '
                 f'forecast average {avg_pred:.2f} per {commodity.unit}).'),
        commodity=commodity,
        market=market,
        severity=severity,
        alert_type='forecast_change',
        previous_price=current,
        current_price=avg_pred,
        percent_change=change,
        recipient_kind='market',
    )


def forecast_prices(market, commodity, horizon=7):
    rows = list(PriceRecord.objects.filter(market=market, commodity=commodity, validated=True).order_by('recorded_at'))
    if not rows:
        rows = list(PriceRecord.objects.filter(market=market, commodity=commodity).order_by('recorded_at'))
    values = [float(r.price) for r in rows]
    if not values:
        return []
    model = 'Trend baseline'
    rmse = None
    preds = []
    try:
        from statsmodels.tsa.arima.model import ARIMA
        if len(values) >= 12:
            fit = ARIMA(values, order=(1, 1, 1)).fit()
            preds = list(map(float, fit.forecast(horizon)))
            model = 'ARIMA(1,1,1)'
        else:
            raise RuntimeError()
    except Exception:
        slope = (values[-1] - values[0]) / max(1, len(values) - 1) if len(values) >= 2 else 0
        base = values[-1]
        preds = [max(0.01, base + slope * (i + 1)) for i in range(horizon)]
    sd = pstdev(values[-min(len(values), 10):]) if len(values) > 1 else max(values[-1] * 0.03, 1)
    last = rows[-1].recorded_at.date()
    out = []
    for i, p in enumerate(preds, 1):
        d = last + timedelta(days=i)
        lower = max(0, p - 1.96 * sd)
        upper = p + 1.96 * sd
        out.append(Forecast.objects.create(
            market=market, commodity=commodity, forecast_date=d,
            predicted_price=round(p, 2), lower_bound=round(lower, 2),
            upper_bound=round(upper, 2), model_name=model, rmse=rmse
        ))
    create_forecast_alerts(market, commodity, out)
    return out


def make_recommendations(commodity, quantity=100):
    markets = list(Market.objects.filter(active=True))
    latest = {}
    for m in markets:
        p = PriceRecord.objects.filter(market=m, commodity=commodity).order_by('-recorded_at').first()
        f = Forecast.objects.filter(market=m, commodity=commodity).order_by('-forecast_date').first()
        latest[m.id] = float(f.predicted_price) if f else float(p.price) if p else None
    recs = []
    for origin in markets:
        if latest.get(origin.id) is None:
            continue
        for dest in markets:
            if origin.id == dest.id or latest.get(dest.id) is None:
                continue
            spread = latest[dest.id] - latest[origin.id]
            transport_cost = 8.0 if origin.name != 'Freetown' and dest.name == 'Freetown' else 5.0
            storage_cost = 2.0 if commodity.storable else 6.0
            margin = spread - transport_cost - storage_cost
            if margin > 0:
                conf = min(0.95, max(0.50, 0.50 + abs(margin) / (abs(latest[dest.id]) + 1) * 0.5))
                rec = Recommendation.objects.create(
                    commodity=commodity, origin=origin, destination=dest,
                    quantity=quantity, action='transport', expected_margin=round(margin, 2),
                    confidence=round(conf, 2),
                    rationale=f'Forecast price difference is {spread:.2f}; estimated transport and storage cost is {transport_cost+storage_cost:.2f}.'
                )
                recs.append(rec)
                if margin >= 10:
                    _create_alerts(
                        title='Market opportunity detected',
                        message=(f'{commodity.name}: move goods from {origin.name} to {dest.name}. '
                                 f'Estimated margin is {margin:.2f} per unit.'),
                        commodity=commodity,
                        market=dest,
                        severity='info',
                        alert_type='opportunity',
                        recipient_kind='opportunity',
                    )
    return recs
