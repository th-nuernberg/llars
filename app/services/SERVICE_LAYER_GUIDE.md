# LLARS Service Layer Guide

## Overview

This guide documents the service layer for LLARS backend. The service layer separates business logic from route handlers, following the principle of separation of concerns.

## Architecture

```
Routes (Presentation Layer)
    ↓
Services (Business Logic Layer)
    ↓
Models (Data Layer)
```

## Available Services

### 1. UserService

**Location:** `app/services/user_service.py`

**Purpose:** Handles all user-related business logic including user creation, API key validation, and user group management.

#### Key Methods

```python
from services import UserService

# Get user by API key
user = UserService.get_user_by_api_key(api_key)

# Get user by username
user = UserService.get_user_by_username(username)

# Validate API key
is_valid, user, error_msg = UserService.validate_api_key(api_key)
if not is_valid:
    return jsonify({'error': error_msg}), 401

# Create a new user
success, user, error_msg = UserService.create_user(
    username="john_doe",
    password="secret123",
    api_key=None,  # Auto-generated if None
    group_name="Standard"
)

# Check if user exists
exists = UserService.user_exists(username)

# Get or create default group
default_group = UserService.get_or_create_default_group()

# Change user group (admin only)
success, error_msg = UserService.change_user_group(
    username="john_doe",
    new_group_name="Admin",
    admin_user=current_admin_user
)

# Validate UUID
is_valid = UserService.validate_uuid(api_key, version=4)
```

---

### 2. ThreadService

**Location:** `app/services/thread_service.py`

**Purpose:** Handles all email thread-related business logic including thread creation, message management, and feature management.

#### Key Methods

```python
from services import ThreadService

# Get thread by ID
thread = ThreadService.get_thread_by_id(thread_id, function_type_id=1)

# Get threads for a user (with scenario-based access control)
threads = ThreadService.get_threads_for_user(user_id, function_type_id=1)

# Check if user can access thread
can_access = ThreadService.can_user_access_thread(user_id, thread_id, function_type_id=1)
if not can_access:
    return jsonify({'error': 'Access denied'}), 403

# Create or update thread
success, thread, error_msg = ThreadService.create_or_update_thread(
    chat_id="chat_123",
    institut_id="inst_456",
    function_type_id=1,
    subject="Email subject",
    sender="sender@example.com"
)

# Add message to thread
success, message, error_msg = ThreadService.add_message_to_thread(
    thread_id=thread.thread_id,
    sender="user@example.com",
    content="Message content",
    timestamp=datetime.now(),
    generated_by="human"
)

# Parse timestamp (handles multiple formats)
timestamp = ThreadService.parse_timestamp("2024-01-15 10:30:00")

# Add feature to thread
success, feature, error_msg = ThreadService.add_feature_to_thread(
    thread_id=thread.thread_id,
    llm_name="gpt-4",
    feature_type_name="situation_summary",
    content={"summary": "..."}
)

# Get thread with all messages and features
thread_data = ThreadService.get_thread_with_messages_and_features(
    thread_id=thread_id,
    function_type_id=1
)

# Map function type input to ID
function_type_id = ThreadService.map_function_type_input("ranking")  # Returns 1

# Get consulting category types
categories = ThreadService.get_consulting_category_types()
```

---

### 3. RankingService

**Location:** `app/services/ranking_service.py`

**Purpose:** Handles all ranking-related business logic including user feature rankings, ranking status, and statistics.

#### Key Methods

```python
from services import RankingService

# Get user rankings for a thread
rankings = RankingService.get_user_rankings_for_thread(user_id, thread_id)

# Check if user has ranked any features in thread
has_ranked = RankingService.has_user_ranked_thread(user_id, thread_id)

# Check if user has fully ranked all features in thread
fully_ranked = RankingService.has_user_fully_ranked_thread(user_id, thread_id)

# Get current rankings organized by type and bucket
rankings_data = RankingService.get_current_rankings_by_type(user_id, thread_id)
# Returns: {"situation_summary": {"goodList": [...], "averageList": [...], ...}}

# Save a ranking
success, error_msg = RankingService.save_ranking(
    user_id=user_id,
    thread_id=thread_id,
    feature_id=feature_id,
    type_id=type_id,
    llm_id=llm_id,
    position=1,
    bucket="Gut"
)

# Get ranking statistics for all users
user_stats = RankingService.get_user_ranking_stats_for_all_users()

# Generate CSV data for rankings export
csv_data = RankingService.generate_rankings_csv_data()
```

---

### 4. FeatureService

**Location:** `app/services/feature_service.py`

**Purpose:** Handles all feature-related business logic including feature types, function types, and LLM management.

#### Key Methods

```python
from services import FeatureService

# Get function type by name
function_type = FeatureService.get_function_type_by_name("ranking")

# Get or create feature type
feature_type = FeatureService.get_or_create_feature_type("situation_summary")

# Get or create LLM
llm = FeatureService.get_or_create_llm("gpt-4")

# Get feature by ID
feature = FeatureService.get_feature_by_id(feature_id)

# Get all features for a thread
features = FeatureService.get_features_by_thread(thread_id)

# Get feature by specific attributes
feature = FeatureService.get_feature_by_attributes(
    thread_id=thread_id,
    type_id=type_id,
    llm_id=llm_id,
    content=None
)

# Get features count for a thread
count = FeatureService.get_features_count_by_thread(thread_id)

# Get features filtered by type
features = FeatureService.get_features_by_type(thread_id, "situation_summary")

# Get features filtered by LLM
features = FeatureService.get_features_by_llm(thread_id, "gpt-4")
```

---

### 5. PermissionService

**Location:** `app/services/permission_service.py`

**Purpose:** Handles all permission-related business logic including permission checking, role management, and audit logging.

#### Key Methods

```python
from services import PermissionService

# Check if user has permission
has_permission = PermissionService.check_permission(
    username="john_doe",
    permission_key="feature:mail_rating:view"
)

# Get all effective permissions for user
permissions = PermissionService.get_user_permissions(username="john_doe")

# Get user roles
roles = PermissionService.get_user_roles(username="john_doe")

# Grant permission
success = PermissionService.grant_permission(
    username="john_doe",
    permission_key="feature:mail_rating:edit",
    admin_username="admin"
)

# Revoke permission
success = PermissionService.revoke_permission(
    username="john_doe",
    permission_key="feature:mail_rating:edit",
    admin_username="admin"
)

# Assign role
success = PermissionService.assign_role(
    username="john_doe",
    role_name="researcher",
    admin_username="admin"
)

# Unassign role
success = PermissionService.unassign_role(
    username="john_doe",
    role_name="researcher",
    admin_username="admin"
)
```

---

## Usage Examples

### Example 1: Create Email Thread with Messages

```python
from services import ThreadService
from flask import request, jsonify

@data_blueprint.route('/email_threads', methods=['POST'])
def create_email_thread():
    data = request.get_json()

    # Map function type
    function_type_id = ThreadService.map_function_type_input(data.get('type', ''))
    if not function_type_id:
        return jsonify({"error": "Invalid function type"}), 400

    # Create or update thread
    success, thread, error = ThreadService.create_or_update_thread(
        chat_id=data.get('chat_id'),
        institut_id=data.get('institut_id'),
        function_type_id=function_type_id,
        subject=data.get('subject'),
        sender=data.get('sender', 'Alias')
    )

    if not success:
        return jsonify({"error": error}), 500

    # Add messages
    for msg_data in data.get('messages', []):
        timestamp = ThreadService.parse_timestamp(msg_data.get('timestamp'))
        if not timestamp:
            continue

        ThreadService.add_message_to_thread(
            thread_id=thread.thread_id,
            sender=msg_data.get('sender'),
            content=msg_data.get('content'),
            timestamp=timestamp,
            generated_by=msg_data.get('generated_by', 'human')
        )

    return jsonify({'status': 'success', 'thread_id': thread.thread_id}), 201
```

### Example 2: User API Key Validation

```python
from services import UserService
from flask import request, jsonify

@data_blueprint.route('/protected_resource', methods=['GET'])
def protected_resource():
    # Get API key from header
    api_key = request.headers.get('Authorization')

    # Validate API key
    is_valid, user, error_msg = UserService.validate_api_key(api_key)
    if not is_valid:
        return jsonify({'error': error_msg}), 401

    # User is authenticated, proceed with business logic
    return jsonify({'message': f'Hello, {user.username}!'}), 200
```

### Example 3: Save Rankings with Service

```python
from services import RankingService, ThreadService, FeatureService
from flask import request, jsonify, g

@data_blueprint.route('/save_ranking/<int:thread_id>', methods=['POST'])
def save_ranking(thread_id):
    user = g.authentik_user

    # Check access
    if not ThreadService.can_user_access_thread(user.id, thread_id, 1):
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()

    for feature_type in data:
        type_name = feature_type['type']
        for detail in feature_type['details']:
            model_name = detail['model_name']
            content = detail['content']
            position = detail['position']
            bucket = detail['bucket']

            # Get feature type
            feature_type_entry = FeatureService.get_feature_type_by_name(type_name)
            if not feature_type_entry:
                return jsonify({'error': f'Feature type {type_name} not found'}), 404

            # Get LLM
            llm_entry = FeatureService.get_llm_by_name(model_name)
            if not llm_entry:
                return jsonify({'error': f'LLM {model_name} not found'}), 404

            # Get feature
            feature = FeatureService.get_feature_by_attributes(
                thread_id=thread_id,
                type_id=feature_type_entry.type_id,
                llm_id=llm_entry.llm_id,
                content=content
            )

            if feature:
                # Save ranking
                success, error_msg = RankingService.save_ranking(
                    user_id=user.id,
                    thread_id=thread_id,
                    feature_id=feature.feature_id,
                    type_id=feature_type_entry.type_id,
                    llm_id=llm_entry.llm_id,
                    position=position,
                    bucket=bucket
                )

                if not success:
                    return jsonify({'error': error_msg}), 500

    return jsonify({'status': 'Ranking saved successfully'}), 201
```

### Example 4: Get Thread with Ranking Status

```python
from services import ThreadService, RankingService
from flask import jsonify, g

@data_blueprint.route('/email_threads/rankings/<int:thread_id>', methods=['GET'])
def get_email_thread_for_rankings(thread_id):
    user = g.authentik_user

    # Check access
    if not ThreadService.can_user_access_thread(user.id, thread_id, 1):
        return jsonify({'error': 'Access denied'}), 403

    # Get thread data
    thread_data = ThreadService.get_thread_with_messages_and_features(thread_id, 1)
    if not thread_data:
        return jsonify({'error': 'Thread not found'}), 404

    # Check if user has ranked this thread
    ranked = RankingService.has_user_ranked_thread(user.id, thread_id)
    thread_data['ranked'] = ranked

    return jsonify(thread_data), 200
```

---

## Best Practices

### 1. Always use services in routes

**Bad:**
```python
@data_blueprint.route('/users/<username>', methods=['GET'])
def get_user(username):
    user = User.query.filter_by(username=username).first()  # Direct DB access
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'username': user.username})
```

**Good:**
```python
@data_blueprint.route('/users/<username>', methods=['GET'])
def get_user(username):
    user = UserService.get_user_by_username(username)  # Service layer
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'username': user.username})
```

### 2. Handle errors from services

Services return tuples with error information. Always check for errors:

```python
success, result, error_msg = UserService.create_user(username, password)
if not success:
    return jsonify({'error': error_msg}), 400
```

### 3. Use type hints

All service methods use type hints for better IDE support and documentation:

```python
from typing import Optional, Tuple

@staticmethod
def get_user_by_id(user_id: int) -> Optional['User']:
    ...
```

### 4. Import models inside methods

To avoid circular imports, models are imported inside service methods:

```python
@staticmethod
def get_user_by_username(username: str) -> Optional['User']:
    from db.models import User  # Import inside method
    return User.query.filter_by(username=username).first()
```

### 5. Keep services stateless

All service methods are static methods. Services don't maintain state:

```python
class UserService:
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional['User']:
        ...
```

---

## Migration Path

When refactoring existing routes to use services:

1. **Identify database queries** in route handlers
2. **Find or create** the appropriate service method
3. **Replace direct DB access** with service calls
4. **Test thoroughly** to ensure behavior is unchanged
5. **Remove unused imports** (e.g., database models from routes)

Example migration:

**Before:**
```python
@data_blueprint.route('/email_threads/<int:thread_id>', methods=['GET'])
def get_thread(thread_id):
    thread = EmailThread.query.filter_by(thread_id=thread_id).first()
    if not thread:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'subject': thread.subject})
```

**After:**
```python
@data_blueprint.route('/email_threads/<int:thread_id>', methods=['GET'])
def get_thread(thread_id):
    thread = ThreadService.get_thread_by_id(thread_id)
    if not thread:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'subject': thread.subject})
```

---

## Testing Services

Services can be tested independently from routes:

```python
import unittest
from services import UserService

class TestUserService(unittest.TestCase):
    def test_validate_uuid(self):
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        invalid_uuid = "not-a-uuid"

        self.assertTrue(UserService.validate_uuid(valid_uuid))
        self.assertFalse(UserService.validate_uuid(invalid_uuid))
```

---

## Next Steps

1. **Refactor existing routes** to use the new service layer
2. **Add more service methods** as needed for specific business logic
3. **Add caching** to frequently-used service methods (e.g., permission checks)
4. **Add service tests** for critical business logic
5. **Document service methods** with comprehensive docstrings

---

## Support

For questions or issues with the service layer, refer to:
- Project documentation: `/Users/philippsteigerwald/PycharmProjects/llars/CLAUDE.md`
- Service source code: `/Users/philippsteigerwald/PycharmProjects/llars/app/services/`
