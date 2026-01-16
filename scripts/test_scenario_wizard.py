#!/usr/bin/env python3
"""
Comprehensive test suite for Scenario Wizard AI Analysis.

Tests the AI-powered data analysis with popular public datasets
to verify correct evaluation type detection and configuration suggestions.
"""

import json
import requests
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:55080"
LOGIN_URL = f"{BASE_URL}/auth/login"
ANALYZE_URL = f"{BASE_URL}/api/ai-assist/analyze-scenario-data"

# Test credentials
USERNAME = "admin"
PASSWORD = "admin123"


# ============================================================================
# POPULAR TEST DATASETS (Based on Web Search Results)
# ============================================================================

DATASETS = {
    # 1. IMDb Movie Reviews - Binary Sentiment (Rating/Labeling)
    "imdb_reviews": {
        "name": "IMDb Movie Reviews",
        "source": "https://huggingface.co/datasets/imdb",
        "expected_type": "rating",  # or labeling for binary
        "expected_preset": "likert-5",  # or binary-sentiment
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
                "response_a": "Here's a simple recipe: Mix 2 cups flour, 2 cups sugar, 3/4 cup cocoa powder. Add eggs, milk, oil, and vanilla. Bake at 350°F for 30-35 minutes.",
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
        "expected_type": "rating",  # or labeling for 5-class
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


def get_auth_token():
    """Authenticate and get session token."""
    session = requests.Session()

    # First, get the login page to establish session
    try:
        # Use the Authentik OAuth flow - simplified for testing
        # In a real test, we'd go through the full OAuth flow
        # For now, we'll try direct API access with session

        # Try to authenticate via the backend directly
        response = session.post(
            f"{BASE_URL}/auth/api-login",
            json={"username": USERNAME, "password": PASSWORD},
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            return session, data.get('access_token')
    except Exception as e:
        print(f"Auth via api-login failed: {e}")

    return session, None


def test_scenario_analysis(session, token, dataset_key, dataset_info):
    """Test the scenario analysis endpoint with a dataset."""
    print(f"\n{'='*60}")
    print(f"Testing: {dataset_info['name']}")
    print(f"Source: {dataset_info['source']}")
    print(f"Expected Type: {dataset_info['expected_type']}")
    print(f"Expected Preset: {dataset_info['expected_preset']}")
    print(f"{'='*60}")

    headers = {
        "Content-Type": "application/json"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {
        "data": dataset_info["data"],
        "filename": f"{dataset_key}.json",
        "file_count": 1,
        "user_hint": dataset_info.get("description", "")
    }

    try:
        response = session.post(
            ANALYZE_URL,
            json=payload,
            headers=headers,
            timeout=60
        )

        if response.status_code == 401:
            print("❌ AUTHENTICATION FAILED (401)")
            return None

        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None

        result = response.json()

        if not result.get('success'):
            print(f"❌ Analysis failed: {result}")
            return None

        analysis = result.get('analysis', {})
        suggestions = analysis.get('suggestions', {})
        data_quality = analysis.get('data_quality', {})

        # Extract results
        detected_type = suggestions.get('evaluation_type', 'UNKNOWN')
        detected_preset = suggestions.get('preset', 'UNKNOWN')
        confidence = suggestions.get('confidence', 0)
        suggested_name = suggestions.get('name', 'N/A')

        # Check if detection matches expectation
        type_match = detected_type.lower() == dataset_info['expected_type'].lower()
        preset_match = detected_preset.lower() == dataset_info['expected_preset'].lower() if detected_preset else False

        print(f"\n📊 RESULTS:")
        print(f"   Detected Type:   {detected_type} {'✅' if type_match else '❌'}")
        print(f"   Detected Preset: {detected_preset} {'✅' if preset_match else '⚠️'}")
        print(f"   Confidence:      {confidence}")
        print(f"   Suggested Name:  {suggested_name}")
        print(f"   Tokens Used:     {result.get('tokens_used', 'N/A')}")

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
            "suggested_name": suggested_name
        }

    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def generate_report(results):
    """Generate a comprehensive test report."""
    print("\n")
    print("=" * 80)
    print("                    SCENARIO WIZARD TEST REPORT")
    print(f"                    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Statistics
    total = len(results)
    type_correct = sum(1 for r in results if r and r['type_match'])
    preset_correct = sum(1 for r in results if r and r['preset_match'])
    failed = sum(1 for r in results if r is None)

    print(f"\n📈 SUMMARY:")
    print(f"   Total Tests:       {total}")
    print(f"   Type Accuracy:     {type_correct}/{total-failed} ({type_correct/(total-failed)*100:.1f}%)" if total > failed else "   N/A")
    print(f"   Preset Accuracy:   {preset_correct}/{total-failed} ({preset_correct/(total-failed)*100:.1f}%)" if total > failed else "   N/A")
    print(f"   Failed Requests:   {failed}")

    # Detailed Results Table
    print(f"\n📊 DETAILED RESULTS:")
    print("-" * 80)
    print(f"{'Dataset':<25} {'Expected':<15} {'Detected':<15} {'Match':<10}")
    print("-" * 80)

    for r in results:
        if r:
            match_symbol = "✅" if r['type_match'] else "❌"
            print(f"{r['name'][:24]:<25} {r['expected_type']:<15} {r['detected_type']:<15} {match_symbol:<10}")
        else:
            print(f"{'FAILED':<25} {'-':<15} {'-':<15} {'❌':<10}")

    print("-" * 80)

    # Recommendations
    print(f"\n💡 ANALYSIS:")

    if type_correct == total - failed:
        print("   ✅ All evaluation types were correctly detected!")
    else:
        print("   ⚠️ Some evaluation types were not correctly detected:")
        for r in results:
            if r and not r['type_match']:
                print(f"      - {r['name']}: Expected '{r['expected_type']}', got '{r['detected_type']}'")

    print("\n" + "=" * 80)

    return {
        "total": total,
        "type_accuracy": type_correct / (total - failed) if total > failed else 0,
        "preset_accuracy": preset_correct / (total - failed) if total > failed else 0,
        "failed": failed
    }


def main():
    """Main test runner."""
    print("🚀 Starting Scenario Wizard Tests")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Test User: {USERNAME}")

    # Authenticate
    print("\n🔐 Authenticating...")
    session, token = get_auth_token()

    if not token:
        print("⚠️ Could not get auth token, trying without authentication...")
    else:
        print("✅ Authentication successful")

    # Run tests
    results = []
    for dataset_key, dataset_info in DATASETS.items():
        result = test_scenario_analysis(session, token, dataset_key, dataset_info)
        results.append(result)

    # Generate report
    summary = generate_report(results)

    # Exit code based on results
    if summary['type_accuracy'] >= 0.8:
        print("\n✅ Tests PASSED (≥80% accuracy)")
        return 0
    else:
        print("\n❌ Tests FAILED (<80% accuracy)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
