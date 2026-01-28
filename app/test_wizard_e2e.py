#!/usr/bin/env python3
"""End-to-end test for Scenario Wizard data import.

Tests that the import pipeline correctly handles:
1. SINGLE_TEXT format (reviews, articles)
2. QA_PAIR format (questions & answers)
3. CONVERSATION format (chat messages)
"""
import sys
sys.path.insert(0, '/app')
import time

print("=" * 60)
print("SCENARIO WIZARD END-TO-END TEST")
print("=" * 60)

# Use timestamp to ensure unique IDs (avoid reusing existing threads)
ts = str(int(time.time()))

# Create simple test data that matches expected formats
SINGLE_TEXT_DATA = [
    {
        "id": f"review_1_{ts}",
        "title": "Great Product Review",
        "text": "This product exceeded my expectations. The quality is outstanding and it arrived on time. I would definitely recommend it to others.",
        "label": "positive"
    },
    {
        "id": f"review_2_{ts}",
        "title": "Disappointing Experience",
        "text": "Unfortunately this product did not meet my needs. The material feels cheap and the instructions were unclear. Would not buy again.",
        "label": "negative"
    },
    {
        "id": f"review_3_{ts}",
        "title": "Average Quality",
        "text": "The product is okay for the price. Nothing special but it works as described. Delivery was fast.",
        "label": "neutral"
    }
]

QA_PAIR_DATA = [
    {
        "id": f"qa_1_{ts}",
        "question": "What is machine learning?",
        "answer": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed."
    },
    {
        "id": f"qa_2_{ts}",
        "question": "How does neural network work?",
        "answer": "Neural networks are computing systems inspired by biological neural networks. They consist of layers of interconnected nodes that process information using connectionist approaches to computation."
    }
]

CONVERSATION_DATA = [
    {
        "id": f"conv_1_{ts}",
        "title": "Customer Support Chat",
        "messages": [
            {"role": "user", "content": "Hi, I need help with my order."},
            {"role": "assistant", "content": "Hello! I'd be happy to help you. Could you please provide your order number?"},
            {"role": "user", "content": "It's ORDER-12345"},
            {"role": "assistant", "content": "Thank you! I found your order. It's currently being processed and will ship tomorrow."}
        ]
    },
    {
        "id": f"conv_2_{ts}",
        "title": "Technical Support",
        "messages": [
            {"role": "user", "content": "My application keeps crashing."},
            {"role": "assistant", "content": "I'm sorry to hear that. Have you tried restarting the application?"},
            {"role": "user", "content": "Yes, but it still crashes after a few minutes."},
            {"role": "assistant", "content": "Let me escalate this to our technical team. They will contact you within 24 hours."}
        ]
    }
]

from main import app

with app.app_context():
    from db import db
    from db.models.scenario import RatingScenarios, EvaluationItem, Message, ScenarioItems
    from services.data_import.import_service import ImportService
    from services.data_import.adapters.generic_adapter import GenericAdapter
    from services.data_import.adapters.base_adapter import TaskType, ItemType

    import_service = ImportService()
    adapter = GenericAdapter()
    all_tests_passed = True

    # =========================================================================
    # TEST 1: SINGLE_TEXT FORMAT
    # =========================================================================
    print("\n" + "-" * 60)
    print("TEST 1: SINGLE_TEXT FORMAT (Reviews)")
    print("-" * 60)

    # Detect structure
    structure = adapter.detect_structure(SINGLE_TEXT_DATA)
    print(f"   Detected type: {structure['detected_item_type']}")
    print(f"   Detected fields: {structure['detected_fields']}")

    # Create session and transform
    session = import_service.create_session_from_data(
        data=SINGLE_TEXT_DATA,
        task_type=TaskType.RATING,
        filename='reviews_test.json'
    )
    session = import_service.transform(session.session_id)
    print(f"   Transform status: {session.status}")
    print(f"   Items parsed: {len(session.transformed_items)}")

    test1_passed = False
    if session.transformed_items:
        first = session.transformed_items[0]
        print(f"   Item type: {first.item_type.value}")
        print(f"   Content preview: {first.content[:60]}...")
        if first.item_type == ItemType.SINGLE_TEXT and first.content and len(first.content) > 50:
            test1_passed = True
            print("   >>> TEST 1 PASSED")
        else:
            print("   !!! TEST 1 FAILED - incorrect item type or content")
    else:
        print("   !!! TEST 1 FAILED - no items transformed")

    all_tests_passed = all_tests_passed and test1_passed

    # =========================================================================
    # TEST 2: QA_PAIR FORMAT
    # =========================================================================
    print("\n" + "-" * 60)
    print("TEST 2: QA_PAIR FORMAT (Q&A)")
    print("-" * 60)

    structure = adapter.detect_structure(QA_PAIR_DATA)
    print(f"   Detected type: {structure['detected_item_type']}")
    print(f"   Detected fields: {structure['detected_fields']}")

    session = import_service.create_session_from_data(
        data=QA_PAIR_DATA,
        task_type=TaskType.RATING,
        filename='qa_test.json'
    )
    session = import_service.transform(session.session_id)
    print(f"   Transform status: {session.status}")
    print(f"   Items parsed: {len(session.transformed_items)}")

    test2_passed = False
    if session.transformed_items:
        first = session.transformed_items[0]
        print(f"   Item type: {first.item_type.value}")
        print(f"   Question: {first.question[:40]}...")
        print(f"   Answer: {first.answer[:40]}...")
        if first.item_type == ItemType.QA_PAIR and first.question and first.answer:
            test2_passed = True
            print("   >>> TEST 2 PASSED")
        else:
            print("   !!! TEST 2 FAILED - incorrect item type or missing Q/A")
    else:
        print("   !!! TEST 2 FAILED - no items transformed")

    all_tests_passed = all_tests_passed and test2_passed

    # =========================================================================
    # TEST 3: CONVERSATION FORMAT
    # =========================================================================
    print("\n" + "-" * 60)
    print("TEST 3: CONVERSATION FORMAT (Chats)")
    print("-" * 60)

    structure = adapter.detect_structure(CONVERSATION_DATA)
    print(f"   Detected type: {structure['detected_item_type']}")
    print(f"   Detected fields: {structure['detected_fields']}")

    session = import_service.create_session_from_data(
        data=CONVERSATION_DATA,
        task_type=TaskType.MAIL_RATING,
        filename='conversations_test.json'
    )
    session = import_service.transform(session.session_id)
    print(f"   Transform status: {session.status}")
    print(f"   Items parsed: {len(session.transformed_items)}")

    test3_passed = False
    if session.transformed_items:
        first = session.transformed_items[0]
        print(f"   Item type: {first.item_type.value}")
        print(f"   Messages count: {len(first.conversation)}")
        if first.conversation:
            print(f"   First message role: {first.conversation[0].role}")
            print(f"   First message: {first.conversation[0].content[:40]}...")
        if first.item_type == ItemType.CONVERSATION and len(first.conversation) >= 2:
            test3_passed = True
            print("   >>> TEST 3 PASSED")
        else:
            print("   !!! TEST 3 FAILED - incorrect item type or no messages")
    else:
        print("   !!! TEST 3 FAILED - no items transformed")

    all_tests_passed = all_tests_passed and test3_passed

    # =========================================================================
    # TEST 4: FULL IMPORT TO DATABASE
    # =========================================================================
    print("\n" + "-" * 60)
    print("TEST 4: FULL DATABASE IMPORT")
    print("-" * 60)

    # Create test scenario
    test_scenario = RatingScenarios(
        scenario_name='Wizard E2E Test',
        function_type_id=2,
        created_by='admin',
        config_json={'eval_type': 'rating'}
    )
    db.session.add(test_scenario)
    db.session.flush()
    print(f"   Created scenario ID: {test_scenario.id}")

    # Import single text data
    session = import_service.create_session_from_data(
        data=SINGLE_TEXT_DATA,
        task_type=TaskType.RATING,
        filename='reviews_test.json'
    )
    session = import_service.transform(session.session_id)
    session = import_service.execute_import(
        session_id=session.session_id,
        task_type=TaskType.RATING,
        source_name='E2E Test Reviews',
        create_scenario=False,
        scenario_id=test_scenario.id
    )
    print(f"   Import status: {session.status}")
    print(f"   Imported count: {session.imported_count}")

    # Fresh query after commit to get current data
    db.session.expire_all()  # Clear session cache
    scenario_items = ScenarioItems.query.filter_by(scenario_id=test_scenario.id).all()
    print(f"   Scenario items linked: {len(scenario_items)}")

    test4_passed = False
    if scenario_items and len(scenario_items) == 3:
        first_item_id = scenario_items[0].item_id
        print(f"   Checking item_id: {first_item_id}")

        # Fresh query for the item
        eval_item = db.session.get(EvaluationItem, first_item_id)
        if eval_item:
            print(f"   EvaluationItem subject: {eval_item.subject[:40]}...")

            # Query messages by item_id
            messages = Message.query.filter_by(item_id=first_item_id).all()
            print(f"   Messages for item: {len(messages)}")

            if messages:
                content = messages[0].content or ''
                print(f"   Content length: {len(content)} chars")
                print(f"   Content preview: {content[:60]}...")

                if len(content) > 50 and not content.startswith('{'):
                    test4_passed = True
                    print("   >>> TEST 4 PASSED")
                else:
                    print("   !!! TEST 4 FAILED - content looks wrong")
            else:
                # Debug: check if messages exist with thread_id
                msgs_by_thread = Message.query.filter_by(thread_id=first_item_id).all()
                print(f"   DEBUG: Messages by thread_id: {len(msgs_by_thread)}")
                print("   !!! TEST 4 FAILED - no messages created")
        else:
            print("   !!! TEST 4 FAILED - no EvaluationItem found")
    else:
        print(f"   !!! TEST 4 FAILED - expected 3 items, got {len(scenario_items)}")

    all_tests_passed = all_tests_passed and test4_passed

    # Cleanup - must delete in correct order due to foreign keys
    print("\n   Cleaning up test data...")
    try:
        # Get item IDs before deleting the links
        item_ids = [si.item_id for si in scenario_items]

        # First delete scenario_items (links) for our test scenario
        ScenarioItems.query.filter_by(scenario_id=test_scenario.id).delete()
        db.session.flush()

        # Delete messages for these items
        for item_id in item_ids:
            Message.query.filter_by(item_id=item_id).delete()
        db.session.flush()

        # Delete evaluation items (only if not linked to other scenarios)
        for item_id in item_ids:
            # Check if item is linked to any other scenario
            other_links = ScenarioItems.query.filter_by(item_id=item_id).count()
            if other_links == 0:
                EvaluationItem.query.filter_by(item_id=item_id).delete()
        db.session.flush()

        # Finally delete the scenario
        db.session.delete(test_scenario)
        db.session.commit()
        print("   Test data cleaned up")
    except Exception as e:
        db.session.rollback()
        print(f"   Cleanup error (non-critical): {str(e)[:50]}...")
        print("   Test data may remain in database")

    # =========================================================================
    # FINAL RESULT
    # =========================================================================
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("ALL TESTS PASSED - Scenario Wizard imports data correctly!")
    else:
        print("SOME TESTS FAILED - Check import logic")
    print("=" * 60)
