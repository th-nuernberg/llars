"""
Error Handler Decorator

Provides @handle_errors decorator for standardized error handling in Flask routes.

Usage:
    @app.route('/api/endpoint')
    @handle_errors(logger_name='my_module')
    def my_endpoint():
        # Your logic - exceptions are automatically caught
        return {'success': True, 'data': result}

The decorator:
1. Catches ValueError and returns 400 Bad Request
2. Catches all other exceptions and returns 500 Internal Server Error
3. Logs errors with the specified logger
4. Returns standardized JSON error responses
"""

from functools import wraps
from flask import jsonify
import logging
from typing import Optional, Callable, Dict, Any, Tuple, Union

# Response type for Flask
FlaskResponse = Tuple[Any, int]


def handle_errors(
    logger_name: Optional[str] = None,
    log_traceback: bool = True,
    custom_handlers: Optional[Dict[type, Callable[[Exception], FlaskResponse]]] = None
):
    """
    Decorator for standardized error handling in Flask routes.

    Args:
        logger_name: Name for the logger (defaults to module name)
        log_traceback: Whether to include traceback in logs (default: True)
        custom_handlers: Dict mapping exception types to handler functions
                        Handler signature: (exception) -> (response, status_code)

    Returns:
        Decorated function with error handling

    Example:
        @app.route('/api/items')
        @handle_errors(logger_name='items')
        def get_items():
            items = ItemService.get_all()
            return jsonify({'success': True, 'items': items})

        # With custom handlers:
        @handle_errors(custom_handlers={
            PermissionError: lambda e: (jsonify({'error': 'Forbidden'}), 403)
        })
        def protected_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get logger
            logger = logging.getLogger(logger_name or f.__module__)

            try:
                return f(*args, **kwargs)

            except ValueError as e:
                # Client error - bad input
                logger.warning(f"ValueError in {f.__name__}: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'error_type': 'validation_error'
                }), 400

            except KeyError as e:
                # Missing required field
                logger.warning(f"KeyError in {f.__name__}: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {str(e)}',
                    'error_type': 'missing_field'
                }), 400

            except Exception as e:
                # Check custom handlers first
                if custom_handlers:
                    for exc_type, handler in custom_handlers.items():
                        if isinstance(e, exc_type):
                            return handler(e)

                # Default: Internal server error
                if log_traceback:
                    logger.error(
                        f"Error in {f.__name__}: {str(e)}",
                        exc_info=True
                    )
                else:
                    logger.error(f"Error in {f.__name__}: {str(e)}")

                return jsonify({
                    'success': False,
                    'error': str(e),
                    'error_type': 'internal_error'
                }), 500

        return decorated_function
    return decorator


def handle_not_found(resource_name: str = 'Resource'):
    """
    Decorator for routes that may return 404.
    Wraps handle_errors and adds None-check for the result.

    Args:
        resource_name: Name of the resource for error message

    Usage:
        @app.route('/api/items/<int:item_id>')
        @handle_not_found('Item')
        def get_item(item_id):
            item = ItemService.get(item_id)
            if not item:
                return None  # Will be converted to 404
            return {'success': True, 'item': item}
    """
    def decorator(f):
        @wraps(f)
        @handle_errors()
        def decorated_function(*args, **kwargs):
            result = f(*args, **kwargs)
            if result is None:
                return jsonify({
                    'success': False,
                    'error': f'{resource_name} not found',
                    'error_type': 'not_found'
                }), 404
            return result
        return decorated_function
    return decorator


class APIError(Exception):
    """
    Custom exception for API errors with status code.

    Usage:
        raise APIError('Invalid configuration', status_code=400)
        raise APIError('Resource not found', status_code=404)
    """
    def __init__(self, message: str, status_code: int = 400, error_type: str = 'api_error'):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type


def handle_api_errors(logger_name: Optional[str] = None):
    """
    Extended decorator that also handles APIError exceptions.

    Usage:
        @handle_api_errors(logger_name='chatbot')
        def create_chatbot():
            if not valid_config:
                raise APIError('Invalid config', status_code=400)
            return {'success': True}
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logger = logging.getLogger(logger_name or f.__module__)

            try:
                return f(*args, **kwargs)

            except APIError as e:
                logger.warning(f"APIError in {f.__name__}: {e.message}")
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'error_type': e.error_type
                }), e.status_code

            except ValueError as e:
                logger.warning(f"ValueError in {f.__name__}: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'error_type': 'validation_error'
                }), 400

            except KeyError as e:
                logger.warning(f"KeyError in {f.__name__}: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {str(e)}',
                    'error_type': 'missing_field'
                }), 400

            except Exception as e:
                logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'error_type': 'internal_error'
                }), 500

        return decorated_function
    return decorator
