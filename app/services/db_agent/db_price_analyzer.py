"""Deutsche Bahn Price Analyzer - rule-based + LLM analysis of collected price data."""

import logging
import math
from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import func, extract, case, literal

from db import db
from db.models.db_agent import DbPriceEntry, DbPriceScan

logger = logging.getLogger(__name__)


def get_price_stats(days_ahead: int = 180) -> dict:
    """Get aggregated price statistics using SQL aggregation (no full load)."""
    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    base_filter = [
        DbPriceEntry.travel_date > today,
        DbPriceEntry.travel_date <= end_date,
    ]

    total = db.session.query(func.count(DbPriceEntry.id)).filter(*base_filter).scalar()
    if not total:
        return {'has_data': False, 'message': 'No price data collected yet. Run a scan first.'}

    def _dir_stats(direction):
        q = db.session.query(
            func.count(DbPriceEntry.id).label('cnt'),
            func.min(DbPriceEntry.price_eur).label('min_p'),
            func.max(DbPriceEntry.price_eur).label('max_p'),
            func.avg(DbPriceEntry.price_eur).label('avg_p'),
        ).filter(*base_filter, DbPriceEntry.direction == direction).first()
        if not q or not q.cnt:
            return None
        return {
            'count': q.cnt,
            'min': round(float(q.min_p), 2),
            'max': round(float(q.max_p), 2),
            'avg': round(float(q.avg_p), 2),
            'median': round(float(q.avg_p), 2),  # approximate with avg
        }

    return {
        'has_data': True,
        'date_range': {'from': str(today + timedelta(days=1)), 'to': str(end_date)},
        'outbound': _dir_stats('outbound'),
        'return': _dir_stats('return'),
        'total_entries': total,
    }


def _deduplicate_entries(entries: list) -> list:
    """Deduplicate entries by (departure, direction), keeping the most recent scan."""
    seen = {}
    for e in entries:
        key = (e.departure.isoformat(), e.direction)
        if key not in seen or e.created_at > seen[key].created_at:
            seen[key] = e
    return sorted(seen.values(), key=lambda e: e.price_eur)


def get_deals(max_results: int = 20) -> list[dict]:
    """Get the cheapest journeys found, sorted by price."""
    max_results = min(max_results, 100)
    today = date.today()

    entries = DbPriceEntry.query.filter(
        DbPriceEntry.travel_date > today,
    ).order_by(
        DbPriceEntry.price_eur.asc()
    ).limit(max_results * 5).all()

    unique = _deduplicate_entries(entries)
    return [_entry_to_dict(e) for e in unique[:max_results]]


def get_deals_for_range(
    date_from: date,
    date_to: date,
    direction: str = None,
    max_results: int = 30,
) -> list[dict]:
    """Get cheapest journeys within a date range."""
    max_results = min(max_results, 100)
    query = DbPriceEntry.query.filter(
        DbPriceEntry.travel_date >= date_from,
        DbPriceEntry.travel_date <= date_to,
    )
    if direction:
        query = query.filter(DbPriceEntry.direction == direction)

    entries = query.order_by(DbPriceEntry.price_eur.asc()).limit(max_results * 5).all()
    unique = _deduplicate_entries(entries)
    return [_entry_to_dict(e) for e in unique[:max_results]]


def get_price_history(travel_date: date, direction: str = 'outbound') -> list[dict]:
    """Get price history for a specific travel date (how prices changed over time)."""
    scans = DbPriceScan.query.filter(
        DbPriceScan.scan_date == travel_date,
        DbPriceScan.direction == direction,
    ).order_by(DbPriceScan.scanned_at.asc()).all()

    return [{
        'scanned_at': s.scanned_at.isoformat(),
        'cheapest_price': s.cheapest_price,
        'journey_count': s.journey_count,
    } for s in scans]


def get_price_volatility() -> list[dict]:
    """Get price volatility per day using SQL aggregation."""
    today = date.today()

    results = db.session.query(
        DbPriceEntry.travel_date,
        DbPriceEntry.direction,
        func.min(DbPriceEntry.price_eur).label('min_p'),
        func.max(DbPriceEntry.price_eur).label('max_p'),
        func.avg(DbPriceEntry.price_eur).label('avg_p'),
        func.count(DbPriceEntry.id).label('cnt'),
    ).filter(
        DbPriceEntry.travel_date > today,
    ).group_by(
        DbPriceEntry.travel_date, DbPriceEntry.direction
    ).order_by(
        DbPriceEntry.travel_date, DbPriceEntry.direction
    ).all()

    # For std_dev we need a second pass — but only fetch price values, not full ORM objects
    result = []
    for r in results:
        avg = float(r.avg_p)
        std_dev = 0.0
        if r.cnt > 1:
            # Fetch only price column for this day+direction to compute std_dev
            prices = [row[0] for row in db.session.query(
                DbPriceEntry.price_eur
            ).filter(
                DbPriceEntry.travel_date == r.travel_date,
                DbPriceEntry.direction == r.direction,
            ).all()]
            if len(prices) > 1:
                variance = sum((p - avg) ** 2 for p in prices) / (len(prices) - 1)
                std_dev = math.sqrt(variance)

        result.append({
            'date': str(r.travel_date),
            'direction': r.direction,
            'min': round(float(r.min_p), 2),
            'max': round(float(r.max_p), 2),
            'avg': round(avg, 2),
            'std_dev': round(std_dev, 2),
            'count': r.cnt,
            'volatile': std_dev > 15,
        })
    return result


def get_calendar_data(direction: str = 'outbound') -> list[dict]:
    """Get cheapest price per day for calendar heatmap (single SQL query + std_dev)."""
    today = date.today()

    results = db.session.query(
        DbPriceEntry.travel_date,
        func.min(DbPriceEntry.price_eur).label('cheapest'),
        func.avg(DbPriceEntry.price_eur).label('average'),
        func.count(DbPriceEntry.id).label('count'),
    ).filter(
        DbPriceEntry.travel_date > today,
        DbPriceEntry.direction == direction,
    ).group_by(
        DbPriceEntry.travel_date
    ).order_by(
        DbPriceEntry.travel_date
    ).all()

    # Batch-fetch all prices grouped by date for std_dev (single query)
    all_prices = db.session.query(
        DbPriceEntry.travel_date,
        DbPriceEntry.price_eur,
    ).filter(
        DbPriceEntry.travel_date > today,
        DbPriceEntry.direction == direction,
    ).all()

    price_by_date = defaultdict(list)
    for row in all_prices:
        price_by_date[row.travel_date].append(row.price_eur)

    calendar = []
    for r in results:
        avg = float(r.average)
        prices = price_by_date.get(r.travel_date, [])
        std_dev = 0.0
        if len(prices) > 1:
            variance = sum((p - avg) ** 2 for p in prices) / (len(prices) - 1)
            std_dev = round(math.sqrt(variance), 2)

        calendar.append({
            'date': str(r.travel_date),
            'cheapest': round(float(r.cheapest), 2),
            'average': round(avg, 2),
            'std_dev': std_dev,
            'count': r.count,
        })
    return calendar


def get_weekday_analysis() -> dict:
    """Analyze price patterns by weekday using SQL aggregation."""
    today = date.today()

    # MariaDB: DAYNAME() returns English weekday names
    results = db.session.query(
        func.dayname(DbPriceEntry.travel_date).label('weekday'),
        func.avg(DbPriceEntry.price_eur).label('avg_p'),
        func.min(DbPriceEntry.price_eur).label('min_p'),
        func.count(DbPriceEntry.id).label('cnt'),
    ).filter(
        DbPriceEntry.travel_date > today,
    ).group_by(
        func.dayname(DbPriceEntry.travel_date)
    ).all()

    result = {}
    for r in results:
        result[r.weekday] = {
            'avg': round(float(r.avg_p), 2),
            'min': round(float(r.min_p), 2),
            'count': r.cnt,
        }
    return result


def get_timing_analysis() -> dict:
    """Analyze price patterns by departure time, booking lead time, and transfer count.

    Uses ALL historical data (including past travel dates) for maximum insight.
    The more scans accumulated over time, the more accurate the analysis.
    """
    total = db.session.query(func.count(DbPriceEntry.id)).scalar()

    if not total:
        return {'has_data': False}

    # --- 1) Departure time of day analysis (SQL: group by hour bucket) ---
    dep_hour = extract('hour', DbPriceEntry.departure)
    time_bucket = case(
        (dep_hour.between(6, 8), '06:00-08:59'),
        (dep_hour.between(9, 11), '09:00-11:59'),
        (dep_hour.between(12, 14), '12:00-14:59'),
        (dep_hour.between(15, 17), '15:00-17:59'),
        (dep_hour.between(18, 21), '18:00-21:59'),
        else_='22:00-05:59',
    )

    dep_results = db.session.query(
        time_bucket.label('slot'),
        func.avg(DbPriceEntry.price_eur).label('avg_p'),
        func.min(DbPriceEntry.price_eur).label('min_p'),
        func.count(DbPriceEntry.id).label('cnt'),
    ).group_by(
        time_bucket
    ).order_by(
        time_bucket
    ).all()

    # Sort in logical time order
    slot_order = ['06:00-08:59', '09:00-11:59', '12:00-14:59',
                  '15:00-17:59', '18:00-21:59', '22:00-05:59']
    dep_map = {r.slot: r for r in dep_results}
    departure_time = []
    for slot in slot_order:
        r = dep_map.get(slot)
        if r:
            departure_time.append({
                'slot': slot,
                'avg': round(float(r.avg_p), 2),
                'min': round(float(r.min_p), 2),
                'median': round(float(r.avg_p), 2),
                'count': r.cnt,
            })

    # --- 2) Booking lead time analysis (uses ALL data for best insights) ---
    # Fetch only needed columns: price, travel_date, scan.scanned_at
    lead_rows = db.session.query(
        DbPriceEntry.price_eur,
        DbPriceEntry.travel_date,
        DbPriceScan.scanned_at,
    ).join(
        DbPriceScan, DbPriceEntry.scan_id == DbPriceScan.id
    ).all()

    lead_buckets = [
        ('1-3 Tage', 1, 3),
        ('4-7 Tage', 4, 7),
        ('1-2 Wochen', 8, 14),
        ('2-4 Wochen', 15, 28),
        ('1-2 Monate', 29, 60),
        ('2-3 Monate', 61, 90),
        ('3+ Monate', 91, 9999),
    ]

    bucket_prices = {label: [] for label, _, _ in lead_buckets}
    date_lead_prices = defaultdict(lambda: defaultdict(list))

    for price, travel_dt, scanned_at in lead_rows:
        lead_days = (travel_dt - scanned_at.date()).days
        if lead_days < 1:
            continue
        for label, lo, hi in lead_buckets:
            if lo <= lead_days <= hi:
                bucket_prices[label].append(price)
                break
        date_lead_prices[str(travel_dt)][lead_days].append(price)

    lead_time = []
    for label, _, _ in lead_buckets:
        prices = bucket_prices[label]
        if prices:
            prices_sorted = sorted(prices)
            lead_time.append({
                'bucket': label,
                'avg': round(sum(prices) / len(prices), 2),
                'min': round(min(prices), 2),
                'median': round(prices_sorted[len(prices_sorted) // 2], 2),
                'count': len(prices),
            })

    # --- 3) Direct vs. transfers analysis (pure SQL, all data) ---
    transfer_results = db.session.query(
        DbPriceEntry.transfers,
        func.avg(DbPriceEntry.price_eur).label('avg_p'),
        func.min(DbPriceEntry.price_eur).label('min_p'),
        func.count(DbPriceEntry.id).label('cnt'),
    ).group_by(
        DbPriceEntry.transfers
    ).order_by(
        DbPriceEntry.transfers
    ).all()

    transfers_analysis = []
    for r in transfer_results:
        t = r.transfers
        label = 'Direkt' if t == 0 else f'{t} Umstieg{"e" if t > 1 else ""}'
        transfers_analysis.append({
            'transfers': t,
            'label': label,
            'avg': round(float(r.avg_p), 2),
            'min': round(float(r.min_p), 2),
            'median': round(float(r.avg_p), 2),
            'count': r.cnt,
        })

    # --- 4) Price trend: avg cheapest price by lead-time bucket ---
    trend_buckets = [
        ('90+ Tage', 90, 9999),
        ('60-90 Tage', 60, 89),
        ('30-60 Tage', 30, 59),
        ('14-30 Tage', 14, 29),
        ('7-14 Tage', 7, 13),
        ('3-7 Tage', 3, 6),
        ('1-3 Tage', 1, 2),
    ]
    trend_data = []
    for label, lo, hi in trend_buckets:
        all_mins = []
        for travel_dt, lead_map in date_lead_prices.items():
            bucket_entries = []
            for ld, prices in lead_map.items():
                if lo <= ld <= hi:
                    bucket_entries.extend(prices)
            if bucket_entries:
                all_mins.append(min(bucket_entries))
        if all_mins:
            trend_data.append({
                'bucket': label,
                'avg_cheapest': round(sum(all_mins) / len(all_mins), 2),
                'min': round(min(all_mins), 2),
                'dates_with_data': len(all_mins),
            })

    return {
        'has_data': True,
        'departure_time': departure_time,
        'lead_time': lead_time,
        'transfers': transfers_analysis,
        'price_trend': trend_data,
        'total_entries': total,
    }


def build_llm_analysis_prompt(
    date_from: date = None,
    date_to: date = None,
) -> str:
    """Build a prompt for LLM analysis of collected price data."""
    stats = get_price_stats()
    if not stats.get('has_data'):
        return None

    deals = get_deals(max_results=10)
    weekday = get_weekday_analysis()
    calendar = get_calendar_data('outbound')

    prompt_parts = [
        'Du bist ein Experte fuer Deutsche Bahn Ticketpreise. Analysiere die folgenden Preisdaten '
        'fuer die Strecke Dortmund Hbf <-> Nuernberg Hbf (BahnCard 25, 2. Klasse, Alter 28).',
        '',
        '## Preisstatistik',
        f'Zeitraum: {stats["date_range"]["from"]} bis {stats["date_range"]["to"]}',
        f'Gesamt-Eintraege: {stats["total_entries"]}',
    ]

    if stats.get('outbound'):
        s = stats['outbound']
        prompt_parts.append(f'Hinfahrt: Min {s["min"]}EUR, Max {s["max"]}EUR, Durchschnitt {s["avg"]}EUR')
    if stats.get('return'):
        s = stats['return']
        prompt_parts.append(f'Rueckfahrt: Min {s["min"]}EUR, Max {s["max"]}EUR, Durchschnitt {s["avg"]}EUR')

    prompt_parts.append('')
    prompt_parts.append('## Top 10 guenstigste Verbindungen')
    for d in deals:
        transfers_info = 'Direkt' if d['is_direct'] else f'{d["transfers"]} Umstiege'
        prompt_parts.append(
            f'- {d["travel_date"]} {d["direction"]}: {d["price_eur"]}EUR, '
            f'{d["departure"][:16]}-{d["arrival"][:16]}, '
            f'{transfers_info}, {d["train_types"]}'
        )

    prompt_parts.append('')
    prompt_parts.append('## Wochentag-Analyse')
    for wd, data in weekday.items():
        prompt_parts.append(f'- {wd}: Durchschnitt {data["avg"]}EUR, Min {data["min"]}EUR ({data["count"]} Verbindungen)')

    prompt_parts.append('')
    prompt_parts.append('## Kalender (guenstigster Preis pro Tag, Hinfahrt)')
    for c in calendar[:14]:
        prompt_parts.append(f'- {c["date"]}: {c["cheapest"]}EUR (Durchschnitt {c["average"]}EUR, {c["count"]} Verbindungen)')

    if date_from and date_to:
        prompt_parts.append('')
        prompt_parts.append(f'## Reisewunsch')
        prompt_parts.append(f'Der Nutzer moechte zwischen {date_from} und {date_to} reisen.')
        prompt_parts.append(f'Suche die besten Verbindungen in diesem Zeitraum (+/- 3 Tage Flexibilitaet).')

        range_deals = get_deals_for_range(
            date_from - timedelta(days=3),
            date_to + timedelta(days=3),
            max_results=15
        )
        if range_deals:
            prompt_parts.append('')
            prompt_parts.append('Guenstigste Verbindungen im Wunschzeitraum:')
            for d in range_deals:
                flexible = '' if (date_from <= date.fromisoformat(d['travel_date']) <= date_to) else ' (flexibel)'
                t_info = 'Direkt' if d['is_direct'] else f'{d["transfers"]} Umstiege'
                prompt_parts.append(
                    f'- {d["travel_date"]}{flexible} {d["direction"]}: {d["price_eur"]}EUR, '
                    f'{d["departure"][:16]}-{d["arrival"][:16]}, {t_info}'
                )

    prompt_parts.extend([
        '',
        '## Aufgabe',
        'Erstelle eine Analyse auf Deutsch mit folgenden Abschnitten:',
        '1. **Preisueberblick**: Wie teuer ist die Strecke generell? Gibt es grosse Preisschwankungen?',
        '2. **Beste Reisetage**: Welche Wochentage/Daten sind am guenstigsten?',
        '3. **Muster & Trends**: Erkennst du Preismuster (Wochenende vs. Wochentag, Tageszeit, etc.)?',
        '4. **Kaufempfehlung**: Wann sollte man zuschlagen? Welche konkreten Verbindungen empfiehlst du?',
        '5. **Nachtverbindungen**: Gibt es guenstige Direktverbindungen nachts?',
    ])

    if date_from and date_to:
        prompt_parts.append(
            f'6. **Reiseempfehlung {date_from} - {date_to}**: '
            f'Konkrete Empfehlung fuer den Wunschzeitraum inkl. Flexibilitaet.'
        )

    prompt_parts.append('')
    prompt_parts.append('Antworte praegnant und praxisnah. Nenne konkrete Preise und Verbindungen.')

    return '\n'.join(prompt_parts)


def analyze_with_llm(
    date_from: date = None,
    date_to: date = None,
    model_id: str = None,
) -> str:
    """Run LLM analysis on collected price data."""
    prompt = build_llm_analysis_prompt(date_from, date_to)
    if not prompt:
        return 'Keine Preisdaten vorhanden. Bitte zuerst einen Scan starten.'

    try:
        from services.llm.llm_client_factory import LLMClientFactory
        client = LLMClientFactory.create(model_id or 'Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506')
        response = client.chat([
            {'role': 'system', 'content': 'Du bist ein hilfreicher Assistent fuer Deutsche Bahn Preisanalysen.'},
            {'role': 'user', 'content': prompt},
        ])
        return response.get('content', 'Keine Antwort vom LLM erhalten.')
    except Exception as e:
        logger.error(f'LLM analysis failed: {e}')
        return f'LLM-Analyse fehlgeschlagen: {str(e)}'


def chat_with_context(
    system_prompt: str,
    user_message: str,
    chat_history: list = None,
    model_id: str = None,
) -> str:
    """Chat-style follow-up about trip suggestions."""
    try:
        from services.llm.llm_client_factory import LLMClientFactory
        client = LLMClientFactory.create(model_id or 'Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506')

        messages = [{'role': 'system', 'content': system_prompt}]
        for msg in (chat_history or []):
            if msg.get('role') in ('user', 'assistant'):
                messages.append({'role': msg['role'], 'content': msg['content']})
        messages.append({'role': 'user', 'content': user_message})

        response = client.chat(messages)
        return response.get('content', 'Keine Antwort vom LLM erhalten.')
    except Exception as e:
        logger.error(f'Chat analysis failed: {e}')
        return f'Entschuldigung, ein Fehler ist aufgetreten: {str(e)}'


def _entry_to_dict(entry: DbPriceEntry) -> dict:
    return {
        'id': entry.id,
        'departure': entry.departure.isoformat(),
        'arrival': entry.arrival.isoformat(),
        'duration_minutes': entry.duration_minutes,
        'transfers': entry.transfers,
        'is_direct': entry.is_direct,
        'train_types': entry.train_types,
        'price_eur': entry.price_eur,
        'direction': entry.direction,
        'travel_date': str(entry.travel_date),
        'is_night': entry.is_night,
        'created_at': entry.created_at.isoformat(),
        'last_seen_at': entry.last_seen_at.isoformat() if entry.last_seen_at else None,
    }
