import traceback
try:
    import json
    import csv
    import sys
    sys.path.insert(0, '/app')

    from main import app
    with app.app_context():
        # Read test data
        data = []
        with open('/app/test_data/df.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 30:  # Get 2-3 groups
                    break
                data.append(row)

        print(f"Loaded {len(data)} rows")
        
        from services.data_import.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer()

        # Generate field mapping
        mapping = analyzer.generate_field_mapping(
            data=data,
            detected_type='ranking',
            detected_format='long',
            filename='df.csv'
        )
        print(f"\nField Mapping: {json.dumps(mapping, indent=2, ensure_ascii=False)[:500]}")

        # Transform data
        transformed = analyzer.transform_long_format_to_ranking(data, mapping)
        print(f"\nTransformed: {len(transformed)} ranking items")
        
        if transformed:
            first_item = transformed[0]
            print(f"\nFirst item:")
            print(f"  ID: {first_item.get('id')}")
            print(f"  Reference type: {first_item.get('reference', {}).get('type')}")
            print(f"  Number of items to rank: {len(first_item.get('items', []))}")
            
            if first_item.get('items'):
                print(f"\n  First variant:")
                variant = first_item['items'][0]
                print(f"    ID: {variant.get('id')}")
                print(f"    Label: {variant.get('label')}")
                print(f"    Content preview: {str(variant.get('content'))[:200]}...")
                print(f"    Source: {variant.get('source')}")

except Exception as e:
    traceback.print_exc()
