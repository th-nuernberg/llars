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
    def __init__(self, message: str, status_code: int = 400, error_type: str = 'api_error', details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}


class NotFoundError(APIError):
    """
    Exception for 404 Not Found errors.

    Usage:
        raise NotFoundError('Chatbot not found')
        raise NotFoundError('Document #123 not found')
    """
    def __init__(self, message: str = 'Resource not found', details: dict = None):
        super().__init__(message, status_code=404, error_type='not_found', details=details)


class ValidationError(APIError):
    """
    Exception for 400 Bad Request / Validation errors.

    Usage:
        raise ValidationError('name and display_name are required')
        raise ValidationError('Invalid email format', details={'field': 'email'})
    """
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=400, error_type='validation_error', details=details)


class UnauthorizedError(APIError):
    """
    Exception for 401 Unauthorized errors.

    Usage:
        raise UnauthorizedError('Invalid credentials')
        raise UnauthorizedError()  # Uses default message
    """
    def __init__(self, message: str = 'Unauthorized', details: dict = None):
        super().__init__(message, status_code=401, error_type='unauthorized', details=details)


class ForbiddenError(APIError):
    """
    Exception for 403 Forbidden errors.

    Usage:
        raise ForbiddenError('Insufficient permissions')
    """
    def __init__(self, message: str = 'Forbidden', details: dict = None):
        super().__init__(message, status_code=403, error_type='forbidden', details=details)


class ConflictError(APIError):
    """
    Exception for 409 Conflict errors (e.g., duplicate resource).

    Usage:
        raise ConflictError('Case with this name already exists')
        raise ConflictError('Duplicate file detected', details={'existing_id': 123})
    """
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=409, error_type='conflict', details=details)


def handle_api_errors(logger_name: Optional[str] = None):
    """
    Extended decorator that also handles APIError exceptions and its subclasses.

    Usage:
        @handle_api_errors(logger_name='chatbot')
        def create_chatbot():
            if not valid_config:
                raise ValidationError('Invalid config')
            return {'success': True}

        @handle_api_errors()
        def get_item(item_id):
            item = Item.query.get(item_id)
            if not item:
                raise NotFoundError(f'Item {item_id} not found')
            return jsonify({'success': True, 'item': item.to_dict()})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logger = logging.getLogger(logger_name or f.__module__)

            try:
                return f(*args, **kwargs)

            except APIError as e:
                # Covers APIError and all subclasses (NotFoundError, ValidationError, etc.)
                logger.warning(f"APIError in {f.__name__}: {e.message}")
                response = {
                    'success': False,
                    'error': e.message,
                    'error_type': e.error_type
                }
                if e.details:
                    response['details'] = e.details
                return jsonify(response), e.status_code

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
