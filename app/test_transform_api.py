import json
import sys
import traceback

sys.path.insert(0, '/app')

try:
    from main import app
    with app.app_context():
        from services.data_import.ai_analyzer import AIAnalyzer
        import csv
        
        # Read test data
        data = []
        with open('/app/test_data/df.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 30:
                    break
                data.append(row)

        print(f"Original data: {len(data)} rows")
        
        # Generate mapping
        analyzer = AIAnalyzer()
        mapping = analyzer.generate_field_mapping(data, 'ranking', 'long', 'df.csv')
        print(f"\nMapping generated:")
        print(f"  format: {mapping.get('format')}")
        print(f"  grouping: {mapping.get('grouping_field')}")
        print(f"  variant: {mapping.get('variant_field')}")
        
        # Transform
        transformed = analyzer.transform_long_format_to_ranking(data, mapping)
        print(f"\nTransformed: {len(transformed)} ranking items")
        
        if transformed:
            item = transformed[0]
            print(f"\nFirst item structure:")
            print(f"  id: {item.get('id')}")
            print(f"  reference.type: {item.get('reference', {}).get('type')}")
            print(f"  items count: {len(item.get('items', []))}")
            
            print(f"\n  Variants to rank:")
            for v in item.get('items', [])[:5]:
                print(f"    - {v.get('label')}: {str(v.get('content'))[:50]}...")

except Exception as e:
    traceback.print_exc()
