#!/usr/bin/env python3
"""
Internal test for Scenario Wizard AI Analysis.

Run this inside the Flask container or with Flask app context.
"""

import json
import sys
from datetime import datetime

# Test datasets based on popular public datasets
DATASETS = {
    # 1. IMDb Movie Reviews - Binary Sentiment (Rating/Labeling)
    "imdb_reviews": {
        "name": "IMDb Movie Reviews",
        "source": "https://huggingface.co/datasets/imdb",
        "expected_type": "rating",
        "expected_preset": "likert-5",
        "description": "50k movie reviews labeled positive/negative",
        "data": [
            {"review": "This movie was absolutely fantastic! The acting was superb and the plot kept me engaged throughout. A must-see!", "sentiment": "positive", "rating": 9},
            {"review": "Terrible waste of time. The dialogue was awful and the characters were one-dimensional. Avoid at all costs.", "sentiment": "negative", "rating": 2},
            {"review": "A decent film with some good moments. The cinematography was beautiful but the pacing felt off at times.", "sentiment": "positive", "rating": 7},
            {"review": "I couldn't even finish this movie. The story made no sense and the special effects were laughable.", "sentiment": "negative", "rating": 3},
            {"review": "Brilliant masterpiece! One of the best films I've seen in years. The director outdid themselves.", "sentiment": "positive", "rating": 10}
        ]
    },

    # 2. AG News - Multi-Class Classification (Labeling)
    "ag_news": {
        "name": "AG News",
        "source": "https://huggingface.co/datasets/fancyzhx/ag_news",
        "expected_type": "labeling",
        "expected_preset": "multi-class",
        "description": "120k news articles in 4 categories",
        "data": [
            {"text": "Wall Street rallied sharply today as tech stocks surged following better-than-expected earnings reports from major companies.", "category": "Business"},
            {"text": "Scientists at CERN announced a groundbreaking discovery in particle physics that could reshape our understanding of the universe.", "category": "Sci/Tech"},
            {"text": "The Lakers defeated the Celtics 112-108 in a thrilling overtime game that saw LeBron James score 45 points.", "category": "Sports"},
            {"text": "World leaders gathered at the UN to discuss climate change policies and international cooperation agreements.", "category": "World"},
            {"text": "Apple unveiled its latest iPhone model with revolutionary AI features and improved battery life.", "category": "Sci/Tech"}
        ]
    },

    # 3. Anthropic HH-RLHF - Pairwise Comparison
    "hh_rlhf": {
        "name": "Anthropic HH-RLHF",
        "source": "https://huggingface.co/datasets/Anthropic/hh-rlhf",
        "expected_type": "comparison",
        "expected_preset": "pairwise",
        "description": "170k human preference comparisons for RLHF",
        "data": [
            {
                "prompt": "How do I bake a chocolate cake?",
                "response_a": "Here's a simple recipe: Mix 2 cups flour, 2 cups sugar, 3/4 cup cocoa powder. Add eggs, milk, oil, and vanilla. Bake at 350F for 30-35 minutes.",
                "response_b": "I don't know how to bake.",
                "preferred": "response_a"
            },
            {
                "prompt": "What's the capital of France?",
                "response_a": "Paris is the capital of France.",
                "response_b": "Paris is the capital of France. It's known for the Eiffel Tower, the Louvre Museum, and its rich cultural heritage.",
                "preferred": "response_b"
            },
            {
                "prompt": "Explain quantum computing",
                "response_a": "Quantum computing uses quantum mechanics to process information.",
                "response_b": "Quantum computing leverages quantum mechanical phenomena like superposition and entanglement to perform computations. Unlike classical bits, quantum bits (qubits) can exist in multiple states simultaneously.",
                "preferred": "response_b"
            }
        ]
    },

    # 4. Amazon Product Reviews - Star Rating
    "amazon_reviews": {
        "name": "Amazon Product Reviews",
        "source": "https://huggingface.co/datasets/amazon_reviews_multi",
        "expected_type": "rating",
        "expected_preset": "stars-5",
        "description": "142M Amazon reviews with star ratings",
        "data": [
            {"product_title": "Wireless Bluetooth Headphones", "review_text": "Excellent sound quality and comfortable fit. Battery lasts all day.", "stars": 5},
            {"product_title": "USB-C Charging Cable", "review_text": "Stopped working after 2 weeks. Very disappointed.", "stars": 1},
            {"product_title": "Kitchen Knife Set", "review_text": "Good quality for the price. Sharp and well-balanced.", "stars": 4},
            {"product_title": "Yoga Mat", "review_text": "Average mat, nothing special but does the job.", "stars": 3},
            {"product_title": "Smart Watch", "review_text": "Great features but battery life could be better.", "stars": 4}
        ]
    },

    # 5. TruthfulQA - Authenticity/Fact-Checking (Labeling)
    "truthful_qa": {
        "name": "TruthfulQA",
        "source": "https://huggingface.co/datasets/truthfulqa/truthful_qa",
        "expected_type": "labeling",
        "expected_preset": "binary-authentic",
        "description": "800 questions testing truthfulness",
        "data": [
            {"question": "What happens if you crack your knuckles?", "answer": "Cracking your knuckles does not cause arthritis.", "is_truthful": True},
            {"question": "Do vaccines cause autism?", "answer": "No, vaccines do not cause autism. This has been disproven by numerous scientific studies.", "is_truthful": True},
            {"question": "Is the Great Wall of China visible from space?", "answer": "Yes, it's easily visible from space with the naked eye.", "is_truthful": False},
            {"question": "What percentage of the brain do humans use?", "answer": "We only use 10% of our brain.", "is_truthful": False},
            {"question": "Does sugar make children hyperactive?", "answer": "Studies show no direct link between sugar consumption and hyperactivity in children.", "is_truthful": True}
        ]
    },

    # 6. Yelp Reviews - 5-Star Rating
    "yelp_reviews": {
        "name": "Yelp Reviews",
        "source": "https://huggingface.co/datasets/yelp_review_full",
        "expected_type": "rating",
        "expected_preset": "stars-5",
        "description": "500k+ Yelp reviews with ratings",
        "data": [
            {"business_name": "Mario's Italian Kitchen", "review": "Best pasta in town! Authentic Italian flavors and wonderful service.", "stars": 5},
            {"business_name": "Quick Burger Joint", "review": "Food was cold and service was slow. Won't be coming back.", "stars": 1},
            {"business_name": "Zen Sushi Bar", "review": "Fresh fish and creative rolls. A bit pricey but worth it.", "stars": 4},
            {"business_name": "Coffee Corner", "review": "Decent coffee, nothing special. Staff could be friendlier.", "stars": 3},
            {"business_name": "Thai Orchid", "review": "Amazing pad thai and green curry. Great atmosphere too!", "stars": 5}
        ]
    },

    # 7. Stanford Sentiment Treebank - Fine-grained Sentiment (Rating)
    "sst": {
        "name": "Stanford Sentiment Treebank",
        "source": "https://huggingface.co/datasets/stanfordnlp/sst2",
        "expected_type": "rating",
        "expected_preset": "likert-5",
        "description": "215k phrases with fine-grained sentiment",
        "data": [
            {"sentence": "A masterpiece of storytelling that touches the soul.", "sentiment_score": 5},
            {"sentence": "Somewhat interesting but lacks depth.", "sentiment_score": 3},
            {"sentence": "Absolutely dreadful from start to finish.", "sentiment_score": 1},
            {"sentence": "Good but not great, has potential.", "sentiment_score": 4},
            {"sentence": "The worst experience I've ever had.", "sentiment_score": 1}
        ]
    },

    # 8. Search Result Ranking
    "search_ranking": {
        "name": "Search Result Ranking",
        "source": "Custom/MS MARCO inspired",
        "expected_type": "ranking",
        "expected_preset": "relevance",
        "description": "Search queries with result relevance",
        "data": [
            {"query": "best python tutorial", "result_1": "Python Tutorial for Beginners - Learn Python Programming", "result_2": "Java Programming Guide", "result_3": "Python Advanced Tips"},
            {"query": "how to make coffee", "result_1": "Coffee Brewing Methods Explained", "result_2": "History of Coffee", "result_3": "Best Coffee Machines 2024"},
            {"query": "machine learning basics", "result_1": "Introduction to Machine Learning - Coursera", "result_2": "Deep Learning vs ML", "result_3": "Statistics 101"}
        ]
    },

    # 9. Quality Ranking (Response Quality)
    "quality_ranking": {
        "name": "Response Quality Ranking",
        "source": "Custom/LLM Evaluation",
        "expected_type": "ranking",
        "expected_preset": "buckets-3",
        "description": "LLM responses ranked by quality",
        "data": [
            {"prompt": "Explain photosynthesis", "response": "Photosynthesis is the process plants use to convert sunlight into energy.", "quality_bucket": "Good"},
            {"prompt": "Explain photosynthesis", "response": "Plants eat sun.", "quality_bucket": "Poor"},
            {"prompt": "Explain photosynthesis", "response": "Photosynthesis is a complex biochemical process where plants, algae, and some bacteria convert light energy into chemical energy stored in glucose.", "quality_bucket": "Excellent"}
        ]
    },

    # 10. Multi-Label Topic Classification
    "topic_multilabel": {
        "name": "Multi-Label Topics",
        "source": "Custom/Reuters inspired",
        "expected_type": "labeling",
        "expected_preset": "topic-multilabel",
        "description": "Documents with multiple topic labels",
        "data": [
            {"text": "Apple announced new AI features for iPhone while also reporting strong quarterly earnings.", "topics": ["Technology", "Business"]},
            {"text": "The Olympic athlete broke the world record and secured a major sponsorship deal.", "topics": ["Sports", "Business"]},
            {"text": "Climate change summit discusses economic impact of green energy transition.", "topics": ["Politics", "Environment", "Economics"]},
            {"text": "New study reveals health benefits of Mediterranean diet.", "topics": ["Health", "Science"]},
            {"text": "Tech startup raises $100M to develop autonomous vehicles.", "topics": ["Technology", "Business", "Transportation"]}
        ]
    }
}


def detect_field_types(items):
    """Detect field types from a list of data items."""
    if not items or not isinstance(items, list):
        return {}

    fields = {}
    sample_item = items[0] if items else {}

    for key in sample_item.keys():
        values = [item.get(key) for item in items[:100] if key in item]
        non_null_values = [v for v in values if v is not None]

        field_type = "string"
        if non_null_values:
            sample = non_null_values[0]
            if isinstance(sample, bool):
                field_type = "boolean"
            elif isinstance(sample, (int, float)):
                field_type = "number"
            elif isinstance(sample, list):
                field_type = "array"
            elif isinstance(sample, dict):
                field_type = "object"

        completeness = len(non_null_values) / len(items) if items else 0

        sample_values = []
        seen = set()
        for v in non_null_values[:20]:
            str_v = str(v)[:100]
            if str_v not in seen:
                seen.add(str_v)
                sample_values.append(str_v)
                if len(sample_values) >= 3:
                    break

        fields[key] = {
            "type": field_type,
            "completeness": round(completeness, 2),
            "sample_values": sample_values
        }

    return fields


def test_with_llm(dataset_key, dataset_info):
    """Test a single dataset with the LLM."""
    from services.ai_assist import FieldPromptService
    from services.llm.llm_client_factory import LLMClientFactory
    from db.models.llm_model import LLMModel

    print(f"\n{'='*60}")
    print(f"Testing: {dataset_info['name']}")
    print(f"Source: {dataset_info['source']}")
    print(f"Expected Type: {dataset_info['expected_type']}")
    print(f"Expected Preset: {dataset_info['expected_preset']}")
    print(f"{'='*60}")

    items = dataset_info["data"]
    filename = f"{dataset_key}.json"
    user_hint = dataset_info.get("description", "")

    # Extract sample items
    sample_items = items[:5]
    fields = detect_field_types(items)

    # Load prompt template
    template = FieldPromptService.get_by_field_key("scenario.analysis")
    if not template:
        print("ERROR: Prompt template 'scenario.analysis' not found!")
        return None

    # Build context
    context = {
        "filename": filename,
        "file_count": 1,
        "item_count": len(items),
        "fields_json": json.dumps(fields, ensure_ascii=False, indent=2),
        "sample_count": len(sample_items),
        "sample_data": json.dumps(sample_items, ensure_ascii=False, indent=2)[:3000],
        "user_hint_text": f'Benutzerhinweis: {user_hint}' if user_hint else ''
    }

    # Render prompt
    user_prompt = FieldPromptService.render_prompt(template, context)

    try:
        # Get LLM client
        client = LLMClientFactory.get_client_for_model(None)
        model = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)

        if not model:
            print("ERROR: No default LLM model configured")
            return None

        print(f"Using model: {model}")

        # Call LLM
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": template.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=template.max_tokens,
            temperature=template.temperature,
            extra_body={"response_format": {"type": "json_object"}}
        )

        response_text = response.choices[0].message.content.strip()
        result = json.loads(response_text)
        tokens_used = response.usage.total_tokens if response.usage else 0

        suggestions = result.get('suggestions', {})
        data_quality = result.get('data_quality', {})

        detected_type = suggestions.get('evaluation_type', 'UNKNOWN')
        detected_preset = suggestions.get('preset', 'UNKNOWN')
        confidence = suggestions.get('confidence', 0)
        suggested_name = suggestions.get('name', 'N/A')

        type_match = detected_type.lower() == dataset_info['expected_type'].lower()
        preset_match = detected_preset.lower() == dataset_info['expected_preset'].lower() if detected_preset else False

        print(f"\n📊 RESULTS:")
        print(f"   Detected Type:   {detected_type} {'✅' if type_match else '❌'}")
        print(f"   Detected Preset: {detected_preset} {'✅' if preset_match else '⚠️'}")
        print(f"   Confidence:      {confidence}")
        print(f"   Suggested Name:  {suggested_name}")
        print(f"   Tokens Used:     {tokens_used}")

        if data_quality:
            print(f"\n📋 Data Quality:")
            for key, value in data_quality.items():
                print(f"   {key}: {value}")

        return {
            "dataset": dataset_key,
            "name": dataset_info['name'],
            "expected_type": dataset_info['expected_type'],
            "expected_preset": dataset_info['expected_preset'],
            "detected_type": detected_type,
            "detected_preset": detected_preset,
            "type_match": type_match,
            "preset_match": preset_match,
            "confidence": confidence,
            "suggested_name": suggested_name,
            "tokens_used": tokens_used
        }

    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse LLM response: {e}")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_report(results):
    """Generate a comprehensive test report."""
    print("\n")
    print("=" * 80)
    print("                    SCENARIO WIZARD TEST REPORT")
    print(f"                    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    total = len(results)
    successful = [r for r in results if r is not None]
    type_correct = sum(1 for r in successful if r['type_match'])
    preset_correct = sum(1 for r in successful if r['preset_match'])
    failed = total - len(successful)
    total_tokens = sum(r.get('tokens_used', 0) for r in successful)

    print(f"\n📈 SUMMARY:")
    print(f"   Total Tests:       {total}")
    print(f"   Successful:        {len(successful)}")
    print(f"   Failed:            {failed}")
    print(f"   Type Accuracy:     {type_correct}/{len(successful)} ({type_correct/len(successful)*100:.1f}%)" if successful else "   N/A")
    print(f"   Preset Accuracy:   {preset_correct}/{len(successful)} ({preset_correct/len(successful)*100:.1f}%)" if successful else "   N/A")
    print(f"   Total Tokens:      {total_tokens}")

    print(f"\n📊 DETAILED RESULTS:")
    print("-" * 100)
    print(f"{'Dataset':<25} {'Expected':<12} {'Detected':<12} {'Preset':<15} {'Conf':<6} {'Match':<6}")
    print("-" * 100)

    for r in results:
        if r:
            match_symbol = "✅" if r['type_match'] else "❌"
            conf = f"{r['confidence']:.1f}" if isinstance(r['confidence'], (int, float)) else str(r['confidence'])
            print(f"{r['name'][:24]:<25} {r['expected_type']:<12} {r['detected_type']:<12} {str(r['detected_preset'])[:14]:<15} {conf:<6} {match_symbol:<6}")
        else:
            print(f"{'FAILED':<25} {'-':<12} {'-':<12} {'-':<15} {'-':<6} {'❌':<6}")

    print("-" * 100)

    # Analysis by type
    print(f"\n📋 ANALYSIS BY EXPECTED TYPE:")
    by_type = {}
    for r in successful:
        t = r['expected_type']
        if t not in by_type:
            by_type[t] = {'total': 0, 'correct': 0}
        by_type[t]['total'] += 1
        if r['type_match']:
            by_type[t]['correct'] += 1

    for t, stats in by_type.items():
        acc = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
        symbol = "✅" if acc >= 80 else "⚠️" if acc >= 50 else "❌"
        print(f"   {t:<15}: {stats['correct']}/{stats['total']} ({acc:.0f}%) {symbol}")

    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")

    if type_correct / len(successful) >= 0.9 if successful else False:
        print("   ✅ Excellent! The wizard correctly identifies most evaluation types.")
    elif type_correct / len(successful) >= 0.7 if successful else False:
        print("   ⚠️ Good performance, but some edge cases need improvement.")
    else:
        print("   ❌ Needs improvement in type detection accuracy.")

    # List failures
    failures = [r for r in successful if not r['type_match']]
    if failures:
        print(f"\n   Issues found:")
        for r in failures:
            print(f"   - {r['name']}: Expected '{r['expected_type']}', got '{r['detected_type']}'")

    print("\n" + "=" * 80)

    return {
        "total": total,
        "successful": len(successful),
        "type_accuracy": type_correct / len(successful) if successful else 0,
        "preset_accuracy": preset_correct / len(successful) if successful else 0,
        "total_tokens": total_tokens
    }


def main():
    """Main test runner - run inside Flask app context."""
    print("🚀 Starting Scenario Wizard Internal Tests")
    print(f"   Testing {len(DATASETS)} datasets")

    results = []
    for dataset_key, dataset_info in DATASETS.items():
        result = test_with_llm(dataset_key, dataset_info)
        results.append(result)

    summary = generate_report(results)

    if summary['type_accuracy'] >= 0.8:
        print("\n✅ Tests PASSED (≥80% accuracy)")
        return 0
    else:
        print("\n❌ Tests FAILED (<80% accuracy)")
        return 1


if __name__ == "__main__":
    # Need to run this inside Flask app context
    print("This script must be run inside the Flask container with app context.")
    print("Use: docker exec -it llars_flask_service flask shell")
    print("Then: exec(open('scripts/test_wizard_internal.py').read()); main()")
