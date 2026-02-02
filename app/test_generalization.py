import json
import sys
import traceback

sys.path.insert(0, '/app')

try:
    from main import app
    with app.app_context():
        from services.data_import.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer()

        # ============================================
        # BEISPIEL 1: Summarization Benchmark
        # ============================================
        print("=" * 60)
        print("BEISPIEL 1: Summarization Benchmark (Long Format)")
        print("=" * 60)
        
        data1 = [
            {"doc_id": "doc_1", "model": "gpt-4", "summary": "Kurze Zusammenfassung von GPT-4...", "source_text": "Der originale Artikel handelt von..."},
            {"doc_id": "doc_1", "model": "claude-3", "summary": "Claude's Zusammenfassung...", "source_text": "Der originale Artikel handelt von..."},
            {"doc_id": "doc_1", "model": "llama-3", "summary": "Llama's Version...", "source_text": "Der originale Artikel handelt von..."},
            {"doc_id": "doc_2", "model": "gpt-4", "summary": "GPT-4 ueber Dokument 2...", "source_text": "Ein anderer Artikel ueber..."},
            {"doc_id": "doc_2", "model": "claude-3", "summary": "Claude ueber Dokument 2...", "source_text": "Ein anderer Artikel ueber..."},
            {"doc_id": "doc_2", "model": "llama-3", "summary": "Llama ueber Dokument 2...", "source_text": "Ein anderer Artikel ueber..."},
        ]
        
        mapping1 = analyzer.generate_field_mapping(data1, 'ranking', 'unknown', 'summarization_benchmark.csv')
        print(f"\nMapping:")
        print(f"  grouping: {mapping1.get('grouping_field')}")
        print(f"  variant: {mapping1.get('variant_field')}")
        print(f"  output: {mapping1.get('output_field')}")
        print(f"  reference: {mapping1.get('reference_field')}")
        
        transformed1 = analyzer.transform_long_format_to_ranking(data1, mapping1)
        print(f"\nTransformiert: {len(transformed1)} Items, je {len(transformed1[0]['items'])} Varianten")
        print(f"Labels: {[item['label'] for item in transformed1[0]['items']]}")

        # ============================================
        # BEISPIEL 2: Q&A Evaluation
        # ============================================
        print("\n" + "=" * 60)
        print("BEISPIEL 2: Q&A Evaluation (Long Format)")
        print("=" * 60)
        
        data2 = [
            {"question_id": 101, "llm_name": "GPT-4o", "answer": "Die Antwort ist 42.", "question": "Was ist der Sinn des Lebens?"},
            {"question_id": 101, "llm_name": "Claude-3.5", "answer": "Eine philosophische Frage...", "question": "Was ist der Sinn des Lebens?"},
            {"question_id": 101, "llm_name": "Gemini", "answer": "Das haengt von der Perspektive ab.", "question": "Was ist der Sinn des Lebens?"},
            {"question_id": 102, "llm_name": "GPT-4o", "answer": "Python ist eine Programmiersprache.", "question": "Was ist Python?"},
            {"question_id": 102, "llm_name": "Claude-3.5", "answer": "Python wurde 1991 entwickelt...", "question": "Was ist Python?"},
            {"question_id": 102, "llm_name": "Gemini", "answer": "Eine Schlange oder Sprache.", "question": "Was ist Python?"},
        ]
        
        mapping2 = analyzer.generate_field_mapping(data2, 'ranking', 'unknown', 'qa_evaluation.json')
        print(f"\nMapping:")
        print(f"  grouping: {mapping2.get('grouping_field')}")
        print(f"  variant: {mapping2.get('variant_field')}")
        print(f"  output: {mapping2.get('output_field')}")
        print(f"  reference: {mapping2.get('reference_field')}")
        
        transformed2 = analyzer.transform_long_format_to_ranking(data2, mapping2)
        print(f"\nTransformiert: {len(transformed2)} Items, je {len(transformed2[0]['items'])} Varianten")

        # ============================================
        # BEISPIEL 3: Code Generation
        # ============================================
        print("\n" + "=" * 60)
        print("BEISPIEL 3: Code Generation Benchmark")
        print("=" * 60)
        
        data3 = [
            {"task_id": "sort_array", "generator": "copilot", "code": "def sort(arr): return sorted(arr)", "prompt": "Write a function to sort an array"},
            {"task_id": "sort_array", "generator": "codewhisperer", "code": "def sort(arr): arr.sort(); return arr", "prompt": "Write a function to sort an array"},
            {"task_id": "sort_array", "generator": "claude-code", "code": "def sort_array(arr): return sorted(arr)", "prompt": "Write a function to sort an array"},
        ]
        
        mapping3 = analyzer.generate_field_mapping(data3, 'ranking', 'unknown', 'code_benchmark.csv')
        print(f"\nMapping:")
        print(f"  grouping: {mapping3.get('grouping_field')}")
        print(f"  variant: {mapping3.get('variant_field')}")
        print(f"  output: {mapping3.get('output_field')}")
        print(f"  reference: {mapping3.get('reference_field')}")
        
        transformed3 = analyzer.transform_long_format_to_ranking(data3, mapping3)
        print(f"\nTransformiert: {len(transformed3)} Items, je {len(transformed3[0]['items'])} Varianten")
        print(f"Labels: {[item['label'] for item in transformed3[0]['items']]}")

        # ============================================
        # BEISPIEL 4: Ungewoehnliche Feldnamen
        # ============================================
        print("\n" + "=" * 60)
        print("BEISPIEL 4: Ungewoehnliche Feldnamen (Deutsch)")
        print("=" * 60)
        
        data4 = [
            {"ref_nummer": "A1", "ki_system": "System-Alpha", "ergebnis": "Ergebnis Alpha", "eingabe": "Testsatz 1"},
            {"ref_nummer": "A1", "ki_system": "System-Beta", "ergebnis": "Ergebnis Beta", "eingabe": "Testsatz 1"},
            {"ref_nummer": "A2", "ki_system": "System-Alpha", "ergebnis": "Noch ein Ergebnis", "eingabe": "Testsatz 2"},
            {"ref_nummer": "A2", "ki_system": "System-Beta", "ergebnis": "Beta Ergebnis 2", "eingabe": "Testsatz 2"},
        ]
        
        mapping4 = analyzer.generate_field_mapping(data4, 'ranking', 'unknown', 'unusual_fields.csv')
        print(f"\nMapping:")
        print(f"  grouping: {mapping4.get('grouping_field')}")
        print(f"  variant: {mapping4.get('variant_field')}")
        print(f"  output: {mapping4.get('output_field')}")
        print(f"  reference: {mapping4.get('reference_field')}")
        
        transformed4 = analyzer.transform_long_format_to_ranking(data4, mapping4)
        print(f"\nTransformiert: {len(transformed4)} Items, je {len(transformed4[0]['items'])} Varianten")

        print("\n" + "=" * 60)
        print("ZUSAMMENFASSUNG: Alle 4 Beispiele erfolgreich transformiert!")
        print("=" * 60)

except Exception as e:
    traceback.print_exc()
