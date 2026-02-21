"""Admin routes module."""

# Import routes to attach them to data_bp
from routes.admin import system_settings_routes
from routes.admin import field_prompts_routes

__all__ = ['system_settings_routes', 'field_prompts_routes']
