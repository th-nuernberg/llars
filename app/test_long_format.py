import traceback
try:
    import json
    import csv
    import sys
    sys.path.insert(0, '/app')

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

    # Test schema detection
    from services.data_import.schema_detector import SchemaDetector
    detector = SchemaDetector()
    result = detector.detect(data, 'df.csv')
    print(f"\nSchema Detection:")
    print(f"  Type: {result.eval_type.value if result.eval_type else None}")
    print(f"  Confidence: {result.confidence}")
    print(f"  Matched fields: {result.matched_fields}")
    print(f"  Reason: {result.reason}")

    # Test AI analyzer long format detection
    from services.data_import.ai_analyzer import AIAnalyzer
    analyzer = AIAnalyzer()
    is_long = analyzer._detect_long_format(data)
    print(f"\nLong Format Detection: {is_long}")

    # Get stats
    stats = analyzer._analyze_long_format_stats(data)
    print(f"\nLong Format Stats:\n{stats}")

except Exception as e:
    traceback.print_exc()
