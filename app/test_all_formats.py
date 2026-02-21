import json
import csv
import sys
import os
import traceback

sys.path.insert(0, '/app')

try:
    from main import app
    with app.app_context():
        from services.data_import.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer()

        test_dir = '/app/test_data/long_format_tests'
        files = sorted(os.listdir(test_dir))
        
        results = []
        
        for filename in files:
            filepath = os.path.join(test_dir, filename)
            print(f"\n{'='*60}")
            print(f"TESTING: {filename}")
            print(f"{'='*60}")
            
            # Load data
            data = []
            if filename.endswith('.csv'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
            elif filename.endswith('.json'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            print(f"Rows: {len(data)}")
            print(f"Fields: {list(data[0].keys()) if data else 'N/A'}")
            
            # Generate mapping
            mapping = analyzer.generate_field_mapping(data, 'ranking', 'unknown', filename)
            
            print(f"\nMAPPING RESULT:")
            print(f"  success: {mapping.get('success')}")
            print(f"  format: {mapping.get('format')}")
            print(f"  grouping_field: {mapping.get('grouping_field')}")
            print(f"  variant_field: {mapping.get('variant_field')}")
            print(f"  output_field: {mapping.get('output_field')}")
            print(f"  reference_field: {mapping.get('reference_field')}")
            
            # Try transformation
            if mapping.get('success') and mapping.get('format') == 'long':
                transformed = analyzer.transform_long_format_to_ranking(data, mapping)
                print(f"\nTRANSFORMATION:")
                print(f"  Original rows: {len(data)}")
                print(f"  Ranking items: {len(transformed)}")
                print(f"  Variants/item: {len(transformed[0]['items']) if transformed else 0}")
                
                if transformed:
                    print(f"  Variant labels: {[i['label'] for i in transformed[0]['items']]}")
                
                results.append({
                    'file': filename,
                    'success': True,
                    'groups': len(transformed),
                    'variants': len(transformed[0]['items']) if transformed else 0
                })
            else:
                results.append({
                    'file': filename,
                    'success': False,
                    'reason': mapping.get('error', 'Format not long')
                })
        
        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        success_count = sum(1 for r in results if r.get('success'))
        print(f"Success: {success_count}/{len(results)}")
        for r in results:
            status = "OK" if r.get('success') else "FAIL"
            detail = f"{r.get('groups')} groups, {r.get('variants')} variants" if r.get('success') else r.get('reason', 'unknown')
            print(f"  [{status}] {r['file']}: {detail}")

except Exception as e:
    traceback.print_exc()
