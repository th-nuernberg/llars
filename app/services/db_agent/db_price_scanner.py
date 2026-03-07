"""Deutsche Bahn Price Scanner - fetches prices directly from bahn.de API.

Uses the official int.bahn.de/web/api/angebote/fahrplan endpoint (same API
that powers the bahn.de website). No API key required.

Rate limit: We enforce max 30 req/min globally to be respectful to the
bahn.de servers (no official rate limit documented for this endpoint).
"""

import logging
import threading
import time
from collections import deque
from datetime import datetime, date, timedelta
from typing import Optional

import requests

from db import db
from db.models.db_agent import DbPriceScan, DbPriceEntry

logger = logging.getLogger(__name__)

# bahn.de internal API (same as used by db-vendo-client dbweb profile)
API_BASE = 'https://int.bahn.de/web/api'
JOURNEYS_ENDPOINT = f'{API_BASE}/angebote/fahrplan'

# Station IDs (IBNR format)
STATION_DORTMUND = '8000080'
STATION_NUERNBERG = '8000284'

# ---------- Global Rate Limiter ----------
# No official rate limit for bahn.de API, but we stay conservative.
_RATE_LIMIT_MAX = 30          # max requests per 60s window
_RATE_LIMIT_WINDOW = 60.0     # window in seconds
_request_timestamps: deque = deque()
_rate_lock = threading.Lock()


def _wait_for_rate_limit():
    """Block until we can make another request without exceeding the rate limit."""
    while True:
        with _rate_lock:
            now = time.monotonic()
            # Remove timestamps older than the window
            while _request_timestamps and _request_timestamps[0] < now - _RATE_LIMIT_WINDOW:
                _request_timestamps.popleft()
            if len(_request_timestamps) < _RATE_LIMIT_MAX:
                _request_timestamps.append(now)
                return
        # Window full — wait a bit
        time.sleep(1.0)


def _is_night_departure(dt: datetime) -> bool:
    """Check if departure is between 22:00 and 06:00."""
    return dt.hour >= 22 or dt.hour < 6


def _parse_bahn_journey(verbindung: dict, direction: str, travel_date: date) -> Optional[dict]:
    """Parse a single journey from the bahn.de API response."""
    abschnitte = verbindung.get('verbindungsAbschnitte', [])
    if not abschnitte:
        return None

    # Price: angebotsPreis (BahnCard price) or abPreisInfo
    preis = verbindung.get('angebotsPreis', {})
    price_eur = preis.get('betrag')
    if price_eur is None:
        return None

    dep_str = abschnitte[0].get('abfahrtsZeitpunkt')
    arr_str = abschnitte[-1].get('ankunftsZeitpunkt')
    if not dep_str or not arr_str:
        return None

    try:
        departure = datetime.fromisoformat(dep_str)
        arrival = datetime.fromisoformat(arr_str)
    except (ValueError, TypeError):
        return None

    duration = verbindung.get('verbindungsDauerInSeconds', 0) // 60
    if duration == 0:
        duration = int((arrival - departure).total_seconds() / 60)

    transfers = verbindung.get('umstiegsAnzahl', 0)

    train_names = []
    for a in abschnitte:
        vm = a.get('verkehrsmittel', {})
        name = vm.get('name', '')
        if name:
            train_names.append(name)

    return {
        'departure': departure,
        'arrival': arrival,
        'duration_minutes': duration,
        'transfers': transfers,
        'is_direct': transfers == 0,
        'train_types': ', '.join(train_names),
        'price_eur': float(price_eur),
        'direction': direction,
        'travel_date': travel_date,
        'is_night': _is_night_departure(departure),
    }


def _build_request_body(
    from_id: str,
    to_id: str,
    departure_str: str,
    max_transfers: Optional[int] = None,
) -> dict:
    """Build the POST body for the bahn.de journey search API."""
    body = {
        'abfahrtsHalt': f'A=1@L={from_id}@',
        'ankunftsHalt': f'A=1@L={to_id}@',
        'anfrageZeitpunkt': departure_str,
        'ankunftSuche': 'ABFAHRT',
        'klasse': 'KLASSE_2',
        'reisende': [{
            'typ': 'ERWACHSENER',
            'anzahl': 1,
            'alter': ['28'],
            'ermaessigungen': [{'art': 'BAHNCARD25', 'klasse': 'KLASSE_2'}],
        }],
        'schnelleVerbindungen': True,
        'sitzplatzOnly': False,
        'reservierungsKontingenteVorhanden': False,
        'deutschlandTicketVorhanden': False,
        'nurDeutschlandTicketVerbindungen': False,
    }
    if max_transfers is not None:
        body['maxUmstiege'] = max_transfers
    return body


def fetch_journeys_for_date(
    travel_date: date,
    direction: str = 'outbound',
    transfers: Optional[int] = None,
    departure_hour: int = 0,
) -> list[dict]:
    """Fetch journeys from the bahn.de API for a specific date.

    Automatically respects the global rate limit (30 req/min).

    Args:
        travel_date: The travel date to search.
        direction: 'outbound' (Dortmund→Nürnberg) or 'return' (Nürnberg→Dortmund).
        transfers: Max transfers (None = no limit, 0 = direct only).
        departure_hour: Hour to start searching from (0-23).
    """
    if direction == 'outbound':
        from_id, to_id = STATION_DORTMUND, STATION_NUERNBERG
    else:
        from_id, to_id = STATION_NUERNBERG, STATION_DORTMUND

    departure_dt = datetime.combine(travel_date, datetime.min.time().replace(hour=departure_hour))
    departure_str = departure_dt.strftime('%Y-%m-%dT%H:%M:%S')

    body = _build_request_body(from_id, to_id, departure_str, transfers)

    # Wait for rate limit slot before making the request
    _wait_for_rate_limit()

    try:
        resp = requests.post(
            JOURNEYS_ENDPOINT,
            json=body,
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Accept': 'application/json',
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f'bahn.de API error for {travel_date} {direction}: {e}')
        return []

    journeys = []
    for v in data.get('verbindungen', []):
        parsed = _parse_bahn_journey(v, direction, travel_date)
        if parsed:
            journeys.append(parsed)
    return journeys


def fetch_full_day(
    travel_date: date,
    direction: str = 'outbound',
    transfers: Optional[int] = 2,
) -> list[dict]:
    """Fetch all journeys for a full day by querying multiple time windows.

    The bahn.de API returns only ~6 results per request, so we query
    multiple start hours to cover the whole day. Results are deduplicated.
    Uses 4 API calls: 06:00, 10:00, 14:00, 18:00.
    """
    all_journeys = []
    seen = set()

    for hour in (6, 10, 14, 18):
        batch = fetch_journeys_for_date(travel_date, direction, transfers=transfers, departure_hour=hour)
        for j in batch:
            key = (j['departure'].isoformat(), j['direction'])
            if key not in seen:
                seen.add(key)
                all_journeys.append(j)

    return all_journeys


def scan_date(travel_date: date, direction: str = 'outbound') -> DbPriceScan:
    """Scan a single date for both day and night connections.

    Night (22:00-06:00): only direct connections.
    Day (06:00-22:00): up to 2 transfers allowed (4 API calls across time windows).
    """
    all_journeys = []

    # Day connections: up to 2 transfers, cover full day
    day_journeys = fetch_full_day(travel_date, direction, transfers=2)
    all_journeys.extend(day_journeys)

    # Night connections: direct only, search from 00:00
    night_journeys_late = fetch_journeys_for_date(travel_date, direction, transfers=0, departure_hour=0)
    for j in night_journeys_late:
        if j['is_night']:
            all_journeys.append(j)

    # Also check evening before (22:00+)
    prev_date = travel_date - timedelta(days=1)
    night_journeys_evening = fetch_journeys_for_date(prev_date, direction, transfers=0, departure_hour=22)
    for j in night_journeys_evening:
        if j['is_night']:
            j['travel_date'] = travel_date  # associate with target travel date
            all_journeys.append(j)

    # De-duplicate by departure time
    seen = set()
    unique_journeys = []
    for j in all_journeys:
        key = (j['departure'].isoformat(), j['direction'])
        if key not in seen:
            seen.add(key)
            unique_journeys.append(j)

    # Save to DB with deduplication
    cheapest = min((j['price_eur'] for j in unique_journeys), default=None)
    scan = DbPriceScan(
        direction=direction,
        scan_date=travel_date,
        journey_count=len(unique_journeys),
        cheapest_price=cheapest,
    )
    db.session.add(scan)
    db.session.flush()

    # Load existing entries for this date+direction to deduplicate
    existing = DbPriceEntry.query.filter_by(
        travel_date=travel_date, direction=direction,
    ).all()
    # Index by (departure_iso, price) for fast lookup
    existing_map = {}
    for e in existing:
        key = (e.departure.isoformat(), e.price_eur)
        existing_map[key] = e

    now = datetime.utcnow()
    new_count = 0
    reused_count = 0
    for j in unique_journeys:
        dedup_key = (j['departure'].isoformat(), j['price_eur'])
        prev = existing_map.get(dedup_key)
        if prev is not None:
            # Same journey, same price — just update last_seen_at
            prev.last_seen_at = now
            reused_count += 1
        else:
            # New journey or price changed — create new entry
            entry = DbPriceEntry(scan_id=scan.id, **j)
            db.session.add(entry)
            new_count += 1

    db.session.commit()
    logger.info(
        f'Scanned {travel_date} {direction}: {len(unique_journeys)} journeys '
        f'(new={new_count}, reused={reused_count}), cheapest={cheapest}'
    )
    return scan


def cleanup_old_data(keep_days: int = 7) -> int:
    """Remove scans and entries for travel dates that have already passed.

    Keeps data for `keep_days` past days (for analysis).
    Returns number of deleted scans.
    """
    cutoff = date.today() - timedelta(days=keep_days)
    old_scans = DbPriceScan.query.filter(DbPriceScan.scan_date < cutoff).all()
    count = len(old_scans)
    for scan in old_scans:
        db.session.delete(scan)  # cascade deletes entries
    if count:
        db.session.commit()
        logger.info(f'Cleaned up {count} old scans (travel dates before {cutoff})')
    return count


def run_full_scan(days_ahead: int = 180) -> dict:
    """Run a complete scan for the next N days, both directions.

    Returns summary stats.
    """
    today = date.today()
    stats = {
        'dates_scanned': 0,
        'total_journeys': 0,
        'cheapest_outbound': None,
        'cheapest_return': None,
        'errors': [],
        'started_at': datetime.utcnow().isoformat(),
    }

    for day_offset in range(1, days_ahead + 1):
        travel_date = today + timedelta(days=day_offset)

        for direction in ('outbound', 'return'):
            try:
                scan = scan_date(travel_date, direction)
                stats['dates_scanned'] += 1
                stats['total_journeys'] += scan.journey_count

                if scan.cheapest_price is not None:
                    key = f'cheapest_{direction}'
                    if stats[key] is None or scan.cheapest_price < stats[key]:
                        stats[key] = scan.cheapest_price
            except Exception as e:
                db.session.rollback()
                logger.error(f'Scan failed for {travel_date} {direction}: {e}')
                stats['errors'].append(f'{travel_date} {direction}: {str(e)}')

    stats['finished_at'] = datetime.utcnow().isoformat()
    return stats


def search_trip_range(
    date_from: date,
    date_to: date,
    flexibility_days: int = 3,
) -> list[dict]:
    """Search for journeys in a date range with flexibility.

    Returns the best journeys found (sorted by price), looking at
    date_from - flexibility_days to date_to + flexibility_days.
    """
    search_start = date_from - timedelta(days=flexibility_days)
    search_end = date_to + timedelta(days=flexibility_days)

    # Don't search dates in the past
    today = date.today()
    if search_start <= today:
        search_start = today + timedelta(days=1)

    all_journeys = []
    current = search_start
    while current <= search_end:
        for direction in ('outbound', 'return'):
            journeys = fetch_journeys_for_date(current, direction, transfers=2, departure_hour=6)
            for j in journeys:
                j['within_requested_range'] = date_from <= current <= date_to
            all_journeys.extend(journeys)

            # Also check direct night connections
            night_journeys = fetch_journeys_for_date(current, direction, transfers=0, departure_hour=0)
            for j in night_journeys:
                if j['is_night']:
                    j['within_requested_range'] = date_from <= current <= date_to
                    all_journeys.append(j)

        current += timedelta(days=1)

    # Sort by price
    all_journeys.sort(key=lambda j: j['price_eur'])
    return all_journeys


def quick_sample(sample_days: int = 5) -> list[dict]:
    """Do a fast live API check for a handful of upcoming days.

    Returns a small set of journeys sorted by price (no DB storage).
    Used to populate the dashboard when no scan data exists yet.
    Only 1 API call per day per direction = 2*sample_days calls total.
    """
    today = date.today()
    all_journeys = []

    for offset in range(1, sample_days + 1):
        travel_date = today + timedelta(days=offset)
        for direction in ('outbound', 'return'):
            journeys = fetch_journeys_for_date(travel_date, direction, transfers=2, departure_hour=6)
            all_journeys.extend(journeys)

    all_journeys.sort(key=lambda j: j['price_eur'])
    return all_journeys
