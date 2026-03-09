#!/usr/bin/env python3
"""
Test to verify that anonymization maintains consistent name replacements across messages.

This demonstrates the fix for the issue where "Luisa" might become "Birgit" in one message
and "Anna" in another message within the same conversation.
"""

from services.anonymize import AnonymizeService


def test_consistency_without_shared_map():
    """
    OLD BEHAVIOR (without fix):
    Each message processed independently - inconsistent replacements
    """
    print("\n" + "="*80)
    print("TEST 1: WITHOUT SHARED MAPPING (OLD BEHAVIOR - INCONSISTENT)")
    print("="*80)

    message1 = "Hallo, ich bin Luisa und wohne in Zürich."
    message2 = "Luisa hat mir gesagt, dass sie Probleme hat."

    # Process messages independently (old way)
    result1 = AnonymizeService.pseudonymize(text=message1, engine='offline')
    result2 = AnonymizeService.pseudonymize(text=message2, engine='offline')

    print(f"\nMessage 1 (original): {message1}")
    print(f"Message 1 (anonymized): {result1['output_text']}")

    print(f"\nMessage 2 (original): {message2}")
    print(f"Message 2 (anonymized): {result2['output_text']}")

    # Find what "Luisa" became in each message
    luisa_replacement_msg1 = None
    luisa_replacement_msg2 = None

    for group in result1['groups']:
        if group['original'] == 'Luisa':
            luisa_replacement_msg1 = group['replacement']

    for group in result2['groups']:
        if group['original'] == 'Luisa':
            luisa_replacement_msg2 = group['replacement']

    print(f"\n⚠️  In message 1, 'Luisa' became: {luisa_replacement_msg1}")
    print(f"⚠️  In message 2, 'Luisa' became: {luisa_replacement_msg2}")

    if luisa_replacement_msg1 != luisa_replacement_msg2:
        print("❌ INCONSISTENT! Different replacements across messages!")
    else:
        print("✓ Consistent (lucky - same random name chosen)")


def test_consistency_with_shared_map():
    """
    NEW BEHAVIOR (with fix):
    Messages share entity map - consistent replacements
    """
    print("\n" + "="*80)
    print("TEST 2: WITH SHARED MAPPING (NEW BEHAVIOR - CONSISTENT)")
    print("="*80)

    message1 = "Hallo, ich bin Luisa und wohne in Zürich."
    message2 = "Luisa hat mir gesagt, dass sie Probleme hat."

    # Process first message
    result1 = AnonymizeService.pseudonymize(text=message1, engine='offline')

    # Build shared entity map from first message
    conversation_entity_map = {}
    for group in result1['groups']:
        group_id = group['group_id']
        conversation_entity_map[group_id] = {
            'replacement': group['replacement'],
            'mode': group['mode']
        }

    # Use same date shift for consistency
    date_shift_days = result1['date_shift_days']

    # Process second message WITH shared map
    result2 = AnonymizeService.pseudonymize(
        text=message2,
        engine='offline',
        group_overrides=conversation_entity_map,
        date_shift_days=date_shift_days
    )

    print(f"\nMessage 1 (original): {message1}")
    print(f"Message 1 (anonymized): {result1['output_text']}")

    print(f"\nMessage 2 (original): {message2}")
    print(f"Message 2 (anonymized): {result2['output_text']}")

    # Find what "Luisa" became in each message
    luisa_replacement_msg1 = None
    luisa_replacement_msg2 = None

    for group in result1['groups']:
        if group['original'] == 'Luisa':
            luisa_replacement_msg1 = group['replacement']

    for group in result2['groups']:
        if group['original'] == 'Luisa':
            luisa_replacement_msg2 = group['replacement']

    print(f"\n✓ In message 1, 'Luisa' became: {luisa_replacement_msg1}")
    print(f"✓ In message 2, 'Luisa' became: {luisa_replacement_msg2}")

    if luisa_replacement_msg1 == luisa_replacement_msg2:
        print("✅ CONSISTENT! Same replacement across all messages!")
    else:
        print("❌ Still inconsistent - something went wrong!")

    # Show the Zürich replacement too
    zurich_replacement_msg1 = None
    for group in result1['groups']:
        if group['original'] == 'Zürich':
            zurich_replacement_msg1 = group['replacement']

    print(f"\nBonus: 'Zürich' became: {zurich_replacement_msg1}")
    print("(Also consistent across messages if it appears again)")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("ANONYMIZATION CONSISTENCY TEST")
    print("="*80)
    print("\nThis test demonstrates the fix for inconsistent name replacements")
    print("across messages in a conversation.")

    test_consistency_without_shared_map()
    test_consistency_with_shared_map()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\nThe fix ensures that when processing a conversation:")
    print("1. A shared entity map is maintained across all messages")
    print("2. This map is passed as 'group_overrides' to each message")
    print("3. Same date shift is used for all messages")
    print("\nResult: 'Luisa' gets the same replacement in ALL messages!")
    print("="*80 + "\n")
