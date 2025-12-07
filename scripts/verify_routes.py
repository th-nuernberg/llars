#!/usr/bin/env python
"""
Route Verification Script

Tests that all blueprints are properly registered after refactoring.
Run this after starting the Flask application.

Usage:
    python scripts/verify_routes.py
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def test_imports():
    """Test that all modules can be imported without errors."""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)

    test_modules = [
        'routes.registry',
        'routes.auth',
        'routes.rating',
        'routes.permissions',
        'routes.comparison',
        'routes.prompts',
        'routes.llm',
        'routes.judge',
        'routes.oncoco',
        'routes.rag',
        'routes.chatbot',
        'routes.crawler',
        'routes.scenarios',
        'routes.kaimo',
    ]

    passed = 0
    failed = 0

    for module_name in test_modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
            passed += 1
        except Exception as e:
            print(f"✗ {module_name}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_registry():
    """Test the blueprint registry."""
    print("\n" + "=" * 60)
    print("Testing Blueprint Registry")
    print("=" * 60)

    try:
        from routes.registry import get_blueprint_info
        info = get_blueprint_info()

        print("\nRegistered Blueprints:")
        for category, blueprints in info.items():
            print(f"\n{category.upper().replace('_', ' ')}:")
            for bp in blueprints:
                print(f"  - {bp['name']:20} {bp['prefix']:25} {bp['description']}")

        print("\n✓ Registry loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Registry failed: {e}")
        return False


def test_blueprints():
    """Test that blueprints are properly defined."""
    print("\n" + "=" * 60)
    print("Testing Blueprint Definitions")
    print("=" * 60)

    blueprints = [
        ('routes.auth', 'auth_bp'),
        ('routes.auth', 'data_bp'),
        ('routes.llm', 'llm_bp'),
        ('routes.judge', 'judge_bp'),
        ('routes.oncoco', 'oncoco_bp'),
        ('routes.rag', 'rag_bp'),
        ('routes.chatbot', 'chatbot_bp'),
        ('routes.crawler', 'crawler_bp'),
        ('routes.kaimo', 'kaimo_bp'),
    ]

    passed = 0
    failed = 0

    for module_name, bp_name in blueprints:
        try:
            module = __import__(module_name, fromlist=[bp_name])
            bp = getattr(module, bp_name)
            print(f"✓ {module_name}.{bp_name}: {bp.name}")
            passed += 1
        except Exception as e:
            print(f"✗ {module_name}.{bp_name}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def check_old_files():
    """Check if old route files still exist."""
    print("\n" + "=" * 60)
    print("Checking for Old Route Files")
    print("=" * 60)

    old_files = [
        'app/routes/RatingRoutes.py',
        'app/routes/RankingRoutes.py',
        'app/routes/PermissionRoutes.py',
        'app/routes/LLMComparisonRoutes.py',
        'app/routes/UserPromptRoutes.py',
        'app/routes/llm_routes.py',
        'app/routes/routes.py',
    ]

    base_dir = os.path.join(os.path.dirname(__file__), '..')

    existing = []
    for file_path in old_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            existing.append(file_path)
            print(f"⚠ {file_path} (can be removed after verification)")

    if not existing:
        print("✓ No old route files found")
    else:
        print(f"\nFound {len(existing)} old route files that can be removed")

    return True


def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("LLARS Route Refactoring Verification")
    print("=" * 60)

    all_passed = True

    # Test imports
    if not test_imports():
        all_passed = False

    # Test registry
    if not test_registry():
        all_passed = False

    # Test blueprints
    if not test_blueprints():
        all_passed = False

    # Check old files
    check_old_files()

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start the application: ./start_llars.sh")
        print("2. Test key endpoints manually")
        print("3. After 1-2 weeks, remove old route files")
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        print("\nPlease check the errors above and fix before deploying.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
