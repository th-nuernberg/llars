"""Deutsche Bahn Price Agent API routes."""

from datetime import date, datetime
from flask import Blueprint, request, jsonify, current_app

from decorators.error_handler import handle_api_errors, ValidationError
from decorators.permission_decorator import require_permission

db_agent_bp = Blueprint('db_agent', __name__, url_prefix='/api/db-agent')


@db_agent_bp.route('/status', methods=['GET'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def get_status():
    """Get agent status (scheduler, last scan, etc.)."""
    from services.db_agent.db_agent_scheduler import get_status
    return jsonify({'success': True, 'data': get_status()})


@db_agent_bp.route('/scan', methods=['POST'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def trigger_scan():
    """Trigger a manual price scan."""
    from services.db_agent.db_agent_scheduler import trigger_manual_scan
    result = trigger_manual_scan(current_app._get_current_object())
    return jsonify({'success': True, 'data': result})


@db_agent_bp.route('/scheduler/start', methods=['POST'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def start_scheduler():
    """Start the periodic scan scheduler."""
    from services.db_agent.db_agent_scheduler import start_scheduler
    started = start_scheduler(current_app._get_current_object())
    if started:
        return jsonify({'success': True, 'message': 'Scheduler started.'})
    return jsonify({'success': False, 'message': 'Scheduler already running.'})


@db_agent_bp.route('/scheduler/stop', methods=['POST'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def stop_scheduler():
    """Stop the periodic scan scheduler."""
    from services.db_agent.db_agent_scheduler import stop_scheduler
    stopped = stop_scheduler()
    if stopped:
        return jsonify({'success': True, 'message': 'Scheduler stopped.'})
    return jsonify({'success': False, 'message': 'Scheduler not running.'})


@db_agent_bp.route('/stats', methods=['GET'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def get_stats():
    """Get aggregated price statistics."""
    from services.db_agent.db_price_analyzer import get_price_stats
    days = request.args.get('days', 30, type=int)
    return jsonify({'success': True, 'data': get_price_stats(days)})


@db_agent_bp.route('/deals', methods=['GET'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def get_deals():
    """Get cheapest journeys found."""
    from services.db_agent.db_price_analyzer import get_deals
    limit = min(request.args.get('limit', 20, type=int), 100)
    return jsonify({'success': True, 'data': get_deals(limit)})


@db_agent_bp.route('/calendar', methods=['GET'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def get_calendar():
    """Get cheapest price per day for calendar heatmap."""
    from services.db_agent.db_price_analyzer import get_calendar_data
    direction = request.args.get('direction', 'outbound')
    return jsonify({'success': True, 'data': get_calendar_data(direction)})


@db_agent_bp.route('/history', methods=['GET'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def get_price_history():
    """Get price history for a specific travel date."""
    from services.db_agent.db_price_analyzer import get_price_history
    travel_date_str = request.args.get('date')
    if not travel_date_str:
        raise ValidationError('Parameter "date" is required (YYYY-MM-DD).')
    try:
        travel_date = date.fromisoformat(travel_date_str)
    except ValueError:
        raise ValidationError('Invalid date format. Use YYYY-MM-DD.')
    direction = request.args.get('direction', 'outbound')
    return jsonify({'success': True, 'data': get_price_history(travel_date, direction)})


@db_agent_bp.route('/volatility', methods=['GET'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def get_volatility():
    """Get price volatility (std deviation) per day."""
    from services.db_agent.db_price_analyzer import get_price_volatility
    return jsonify({'success': True, 'data': get_price_volatility()})


@db_agent_bp.route('/weekday-analysis', methods=['GET'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def get_weekday_analysis():
    """Get price patterns by weekday."""
    from services.db_agent.db_price_analyzer import get_weekday_analysis
    return jsonify({'success': True, 'data': get_weekday_analysis()})


@db_agent_bp.route('/timing', methods=['GET'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def get_timing():
    """Get timing analysis (departure time, lead time, transfers)."""
    from services.db_agent.db_price_analyzer import get_timing_analysis
    return jsonify({'success': True, 'data': get_timing_analysis()})


@db_agent_bp.route('/analyze', methods=['POST'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def analyze():
    """Run LLM analysis or chat-style follow-up on price data."""
    from services.db_agent.db_price_analyzer import analyze_with_llm, chat_with_context
    data = request.get_json(silent=True) or {}

    # Chat mode: follow-up questions about suggestions
    if data.get('_chat_mode'):
        result = chat_with_context(
            system_prompt=data.get('_system_prompt', ''),
            user_message=data.get('_user_message', ''),
            chat_history=data.get('_chat_history', []),
            model_id=data.get('model_id'),
        )
        return jsonify({'success': True, 'data': {'analysis': result}})

    date_from = None
    date_to = None
    if data.get('date_from'):
        try:
            date_from = date.fromisoformat(data['date_from'])
        except ValueError:
            raise ValidationError('Invalid date_from format. Use YYYY-MM-DD.')
    if data.get('date_to'):
        try:
            date_to = date.fromisoformat(data['date_to'])
        except ValueError:
            raise ValidationError('Invalid date_to format. Use YYYY-MM-DD.')

    model_id = data.get('model_id')
    result = analyze_with_llm(date_from, date_to, model_id)
    return jsonify({'success': True, 'data': {'analysis': result}})


@db_agent_bp.route('/quick-overview', methods=['GET'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def quick_overview():
    """Return a quick overview for the dashboard.

    If scan data exists in the DB, return it. Otherwise do a fast
    live API sample (5 days, both directions) so the page isn't empty.
    """
    from services.db_agent.db_price_analyzer import get_deals, get_price_stats
    from services.db_agent.db_agent_scheduler import get_status as get_agent_status

    stats = get_price_stats()
    agent_status = get_agent_status()

    if stats.get('has_data'):
        deals = get_deals(max_results=15)
        return jsonify({
            'success': True,
            'data': {
                'source': 'database',
                'stats': stats,
                'deals': deals,
                'status': agent_status,
            }
        })

    # No DB data yet — do a quick live sample
    from services.db_agent.db_price_scanner import quick_sample
    sample = quick_sample(sample_days=5)
    sample_dicts = []
    for j in sample[:20]:
        j_copy = dict(j)
        j_copy['departure'] = j_copy['departure'].isoformat()
        j_copy['arrival'] = j_copy['arrival'].isoformat()
        j_copy['travel_date'] = str(j_copy['travel_date'])
        sample_dicts.append(j_copy)

    return jsonify({
        'success': True,
        'data': {
            'source': 'live_sample',
            'stats': {'has_data': False},
            'deals': sample_dicts,
            'status': agent_status,
        }
    })


@db_agent_bp.route('/data', methods=['DELETE'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def delete_all_data():
    """Delete all historical price data."""
    from db import db as _db
    from db.models.db_agent import DbPriceEntry, DbPriceScan
    count_entries = DbPriceEntry.query.delete()
    count_scans = DbPriceScan.query.delete()
    _db.session.commit()
    return jsonify({
        'success': True,
        'message': f'Deleted {count_entries} entries and {count_scans} scans.',
    })


@db_agent_bp.route('/trip-search-live', methods=['POST'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def trip_search_live():
    """Fetch live prices for a single date + direction (4 API calls covering full day).

    Used by the frontend to stream results day-by-day.
    """
    from services.db_agent.db_price_scanner import fetch_full_day

    data = request.get_json(silent=True) or {}
    if not data.get('date') or not data.get('direction'):
        raise ValidationError('date and direction are required.')

    try:
        travel_date = date.fromisoformat(data['date'])
    except ValueError:
        raise ValidationError('Invalid date format. Use YYYY-MM-DD.')

    direction = data['direction']
    journeys = fetch_full_day(travel_date, direction, transfers=2)

    result = []
    for j in journeys:
        result.append({
            'departure': j['departure'].isoformat(),
            'arrival': j['arrival'].isoformat(),
            'duration_minutes': j['duration_minutes'],
            'transfers': j['transfers'],
            'is_direct': j['is_direct'],
            'train_types': j['train_types'],
            'price_eur': j['price_eur'],
            'direction': j['direction'],
            'travel_date': str(j['travel_date']),
            'is_night': j['is_night'],
            'source': 'live',
        })

    return jsonify({'success': True, 'data': {'journeys': result}})


@db_agent_bp.route('/trip-search', methods=['POST'])
@require_permission('feature:db_agent:view')
@handle_api_errors(logger_name='db_agent')
def trip_search():
    """Search for best connections in a date range.

    Always fetches fresh live prices from the API for the exact searched
    dates (1 API call per direction per day, max 3 days). Merges with
    existing DB data, deduplicating by departure time.
    """
    from services.db_agent.db_price_analyzer import get_deals_for_range
    from services.db_agent.db_price_scanner import fetch_journeys_for_date

    data = request.get_json(silent=True) or {}

    if not data.get('date_from') or not data.get('date_to'):
        raise ValidationError('date_from and date_to are required (YYYY-MM-DD).')

    try:
        date_from = date.fromisoformat(data['date_from'])
        date_to = date.fromisoformat(data['date_to'])
    except ValueError:
        raise ValidationError('Invalid date format. Use YYYY-MM-DD.')

    flexibility = data.get('flexibility_days', 3)
    direction = data.get('direction')  # 'outbound' or 'return' or None
    from datetime import timedelta
    search_from = date_from - timedelta(days=flexibility)
    search_to = date_to + timedelta(days=flexibility)

    today = date.today()
    directions = [direction] if direction else ['outbound', 'return']

    # 1) Fetch fresh live prices for the core searched dates (max 7 days)
    live_journeys = []
    live_start = max(date_from, today + timedelta(days=1))
    live_end = min(date_to, live_start + timedelta(days=6))
    current = live_start
    while current <= live_end:
        for d in directions:
            fetched = fetch_journeys_for_date(current, d, transfers=2, departure_hour=6)
            for j in fetched:
                j['within_requested_range'] = date_from <= current <= date_to
                j['source'] = 'live'
                j['departure'] = j['departure'].isoformat()
                j['arrival'] = j['arrival'].isoformat()
                j['travel_date'] = str(j['travel_date'])
            live_journeys.extend(fetched)
        current += timedelta(days=1)

    # 2) Also get historical DB data for the full range (with flexibility)
    db_journeys = get_deals_for_range(search_from, search_to, direction=direction, max_results=100)
    for j in db_journeys:
        td = date.fromisoformat(j['travel_date'])
        j['within_requested_range'] = date_from <= td <= date_to
        j['source'] = 'database'

    # 3) Merge: deduplicate by (departure, direction), prefer live data
    seen = {}
    for j in live_journeys:
        key = (j['departure'][:16], j.get('direction', ''))
        seen[key] = j
    for j in db_journeys:
        key = (j['departure'][:16], j.get('direction', ''))
        if key not in seen:
            seen[key] = j

    merged = sorted(seen.values(), key=lambda j: float(j['price_eur']))

    source = 'live' if live_journeys else ('database' if db_journeys else 'empty')

    return jsonify({
        'success': True,
        'data': {
            'source': source,
            'journeys': merged[:50],
            'total_found': len(merged),
            'search_range': {
                'from': str(date_from),
                'to': str(date_to),
                'flexibility_days': flexibility,
            }
        }
    })
