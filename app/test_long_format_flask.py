import traceback
try:
    import json
    import csv
    import sys
    sys.path.insert(0, '/app')

    from main import app
    with app.app_context():
        # Read some test data
        data = []
        with open('/app/test_data/df.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 15:
                    break
                data.append(row)

        print(f"Loaded {len(data)} rows from df.csv")
        print(f"Fields: {list(data[0].keys()) if data else 'no data'}")

        # Test AI analyzer long format detection
        from services.data_import.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer()
        is_long = analyzer._detect_long_format(data)
        print(f"\nLong Format Detection: {is_long}")

        # Get stats
        stats = analyzer._analyze_long_format_stats(data)
        print(f"\nLong Format Stats:\n{stats}")

        # Test field mapping generation
        print("\n--- Testing field mapping generation ---")
        mapping_result = analyzer.generate_field_mapping(
            data=data,
            detected_type='ranking',
            detected_format='long',
            filename='df.csv'
        )
        print(f"\nField Mapping Result:")
        print(json.dumps(mapping_result, indent=2, ensure_ascii=False))

except Exception as e:
    traceback.print_exc()
