"""
Demo Video Admin API Routes

Admin-only endpoints for managing demo video data (IJCAI 2026).
Protected by system admin API key.

Usage:
    curl -H "X-API-Key: <SYSTEM_ADMIN_API_KEY>" https://host/api/demo-video/status
    curl -X POST -H "X-API-Key: <SYSTEM_ADMIN_API_KEY>" https://host/api/demo-video/seed
    curl -X POST -H "X-API-Key: <SYSTEM_ADMIN_API_KEY>" https://host/api/demo-video/cleanup
    curl -X POST -H "X-API-Key: <SYSTEM_ADMIN_API_KEY>" https://host/api/demo-video/reset
"""

from flask import Blueprint, jsonify
from auth.decorators import system_api_key_required

demo_video_bp = Blueprint('demo_video', __name__, url_prefix='/api/demo-video')


@demo_video_bp.route('/status', methods=['GET'])
@system_api_key_required
def status():
    from services.demo_video_service import get_status
    result = get_status()
    if 'error' in result:
        return jsonify({'success': False, **result}), 404
    return jsonify({'success': True, **result})


@demo_video_bp.route('/seed', methods=['POST'])
@system_api_key_required
def seed():
    from services.demo_video_service import seed as do_seed
    result = do_seed()
    code = 200 if result.get('success') else 500
    return jsonify(result), code


@demo_video_bp.route('/cleanup', methods=['POST'])
@system_api_key_required
def cleanup():
    from services.demo_video_service import cleanup as do_cleanup
    result = do_cleanup()
    return jsonify(result)


@demo_video_bp.route('/cleanup-live-prompt', methods=['POST'])
@system_api_key_required
def cleanup_live_prompt():
    from services.demo_video_service import cleanup_live_prompt_only
    result = cleanup_live_prompt_only()
    return jsonify(result)


@demo_video_bp.route('/reset', methods=['POST'])
@system_api_key_required
def reset():
    from services.demo_video_service import reset as do_reset
    result = do_reset()
    code = 200 if result.get('success') else 500
    return jsonify(result), code
