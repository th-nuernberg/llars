"""
OnCoCo Analysis Service

Provides sentence-level classification of counseling conversations
using the OnCoCo (Online Counseling Conversations) XLM-RoBERTa model.

Model: xlm-roberta-large-OnCoCo-DE-EN
- 68 categories (40 counselor, 28 client)
- Bilingual (German/English)
- ~80% accuracy, F1 Macro 0.78
"""

import logging
import os
import json
import numpy as np
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict

from .oncoco_labels import (
    ONCOCO_LABELS,
    LABEL_HIERARCHY,
    get_label_level2,
    get_label_display_name,
    get_label_role
)

logger = logging.getLogger(__name__)

# Model path - configurable via environment variable
DEFAULT_MODEL_PATH = os.environ.get(
    'ONCOCO_MODEL_PATH',
    "Ideen und Daten dazu/OnCoCo Analyse/xlm-roberta-large-OnCoCo-DE-EN"
)


@dataclass
class ClassificationResult:
    """Result of a single sentence classification."""
    sentence: str
    label: str
    label_level2: str
    confidence: float
    role: str  # counselor or client
    top_3: List[Tuple[str, float]]  # top 3 predictions with confidence


@dataclass
class MessageAnalysis:
    """Analysis result for a single message."""
    message_id: int
    sender: str
    role: str  # counselor or client
    sentences: List[ClassificationResult]
    dominant_label: str
    dominant_label_level2: str
    avg_confidence: float


@dataclass
class ThreadAnalysis:
    """Complete analysis of an email thread."""
    thread_id: int
    pillar_number: int
    messages: List[MessageAnalysis]
    label_distribution: Dict[str, int]
    label_distribution_level2: Dict[str, int]
    transition_matrix: Dict[str, Dict[str, int]]  # label -> label -> count
    total_sentences: int
    counselor_sentences: int
    client_sentences: int


class OnCoCoService:
    """
    Service for analyzing counseling conversations with OnCoCo model.

    Provides:
    - Sentence-level classification
    - Transition matrix computation
    - Label distribution analysis
    - Pillar comparison
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the OnCoCo service.

        Args:
            model_path: Path to the model directory. If None, uses default.
        """
        self.model_path = model_path or self._get_default_model_path()
        self._model = None
        self._tokenizer = None
        self._sentence_tokenizer = None
        self._device = None
        self._id2label = None
        self._label2id = None

    def _get_default_model_path(self) -> str:
        """Get the default model path relative to project root."""
        # Try multiple possible locations
        possible_paths = [
            DEFAULT_MODEL_PATH,
            os.path.join(os.getcwd(), DEFAULT_MODEL_PATH),
            os.path.join("/app", DEFAULT_MODEL_PATH),  # Docker container
            os.path.join(os.path.dirname(__file__), "..", "..", "..", DEFAULT_MODEL_PATH),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return DEFAULT_MODEL_PATH

    def _load_model(self):
        """Lazy load the model and tokenizer."""
        if self._model is not None:
            return

        logger.info(f"[OnCoCo] Loading model from {self.model_path}")

        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            # Determine device
            if torch.cuda.is_available():
                self._device = torch.device("cuda")
                logger.info("[OnCoCo] Using CUDA GPU")
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self._device = torch.device("mps")
                logger.info("[OnCoCo] Using Apple MPS")
            else:
                self._device = torch.device("cpu")
                logger.info("[OnCoCo] Using CPU")

            # Load tokenizer and model
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
            self._model.to(self._device)
            self._model.eval()

            # Load label mappings from config
            config_path = os.path.join(self.model_path, "config.json")
            with open(config_path, 'r') as f:
                config = json.load(f)
                self._id2label = {int(k): v for k, v in config.get('id2label', {}).items()}
                self._label2id = config.get('label2id', {})

            logger.info(f"[OnCoCo] Model loaded successfully. {len(self._id2label)} labels available")

        except ImportError as e:
            logger.error(f"[OnCoCo] Failed to import required packages: {e}")
            raise RuntimeError("Missing dependencies: torch, transformers. Install with: pip install torch transformers")
        except Exception as e:
            logger.error(f"[OnCoCo] Failed to load model: {e}")
            raise

    def _load_sentence_tokenizer(self):
        """Load NLTK sentence tokenizer."""
        if self._sentence_tokenizer is not None:
            return

        try:
            import nltk

            # Ensure punkt tokenizer is available
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                logger.info("[OnCoCo] Downloading NLTK punkt tokenizer")
                nltk.download('punkt', quiet=True)

            # Try punkt_tab for newer NLTK versions
            try:
                nltk.data.find('tokenizers/punkt_tab')
            except LookupError:
                try:
                    nltk.download('punkt_tab', quiet=True)
                except:
                    pass  # Not all NLTK versions have punkt_tab

            self._sentence_tokenizer = nltk.sent_tokenize
            logger.info("[OnCoCo] NLTK sentence tokenizer loaded")

        except ImportError:
            logger.warning("[OnCoCo] NLTK not available, using basic sentence splitting")
            self._sentence_tokenizer = self._basic_sentence_split

    def _basic_sentence_split(self, text: str) -> List[str]:
        """Basic sentence splitting fallback."""
        import re
        # Split on sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def get_hardware_info(self) -> Dict[str, Any]:
        """Get detailed hardware information for the analysis."""
        import platform
        import psutil

        info = {
            'device_type': 'unknown',
            'device_name': 'Unknown',
            'cpu_count': psutil.cpu_count(logical=False) or 1,
            'cpu_count_logical': psutil.cpu_count(logical=True) or 1,
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'memory_used_gb': round(psutil.virtual_memory().used / (1024**3), 2),
            'memory_percent': psutil.virtual_memory().percent,
            'platform': platform.system(),
            'python_version': platform.python_version(),
            'model_loaded': self._model is not None,
        }

        if self._model is not None:
            try:
                import torch
                if self._device.type == 'cuda':
                    info['device_type'] = 'GPU (CUDA)'
                    info['device_name'] = torch.cuda.get_device_name(0)
                    info['gpu_memory_total_gb'] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
                    info['gpu_memory_used_gb'] = round(torch.cuda.memory_allocated(0) / (1024**3), 2)
                elif self._device.type == 'mps':
                    info['device_type'] = 'GPU (Apple MPS)'
                    info['device_name'] = 'Apple Silicon GPU'
                else:
                    info['device_type'] = 'CPU'
                    info['device_name'] = platform.processor() or 'Unknown CPU'

                # Model info
                info['model_parameters'] = sum(p.numel() for p in self._model.parameters())
                info['model_size_mb'] = round(sum(p.numel() * p.element_size() for p in self._model.parameters()) / (1024**2), 2)
            except Exception as e:
                logger.warning(f"[OnCoCo] Could not get detailed hardware info: {e}")

        return info

    def is_model_available(self) -> bool:
        """Check if the model files are available."""
        if not os.path.exists(self.model_path):
            return False

        required_files = ['config.json', 'model.safetensors']
        for f in required_files:
            if not os.path.exists(os.path.join(self.model_path, f)):
                # Also check for pytorch_model.bin as alternative
                if f == 'model.safetensors':
                    if not os.path.exists(os.path.join(self.model_path, 'pytorch_model.bin')):
                        return False
                else:
                    return False
        return True

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_path": self.model_path,
            "model_available": self.is_model_available(),
            "model_loaded": self._model is not None,
            "device": str(self._device) if self._device else None,
            "num_labels": len(self._id2label) if self._id2label else 68,
            "label_hierarchy_levels": len(LABEL_HIERARCHY),
        }

    def classify_sentence(self, sentence: str, role_hint: Optional[str] = None) -> ClassificationResult:
        """
        Classify a single sentence.

        Args:
            sentence: The sentence to classify
            role_hint: Optional hint about the speaker role ('counselor' or 'client')

        Returns:
            ClassificationResult with label, confidence, and top-3 predictions
        """
        self._load_model()

        import torch
        import torch.nn.functional as F

        # Tokenize
        inputs = self._tokenizer(
            sentence,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        # Inference
        with torch.no_grad():
            outputs = self._model(**inputs)
            logits = outputs.logits
            probs = F.softmax(logits, dim=-1)

        # Get predictions
        probs_np = probs.cpu().numpy()[0]
        top_indices = np.argsort(probs_np)[::-1][:3]

        predicted_id = top_indices[0]
        predicted_label = self._id2label.get(predicted_id, f"UNKNOWN_{predicted_id}")
        confidence = float(probs_np[predicted_id])

        # Get top 3
        top_3 = [
            (self._id2label.get(idx, f"UNKNOWN_{idx}"), float(probs_np[idx]))
            for idx in top_indices
        ]

        # Determine role
        role = get_label_role(predicted_label)

        # If role hint provided and doesn't match, check if alternative label fits better
        if role_hint and role != role_hint:
            # Filter for labels matching the role hint
            role_prefix = "CO-" if role_hint == "counselor" else "CL-"
            for idx in top_indices:
                label = self._id2label.get(idx, "")
                if label.startswith(role_prefix):
                    predicted_label = label
                    confidence = float(probs_np[idx])
                    role = role_hint
                    break

        return ClassificationResult(
            sentence=sentence,
            label=predicted_label,
            label_level2=get_label_level2(predicted_label),
            confidence=confidence,
            role=role,
            top_3=top_3
        )

    def classify_sentences_batch(
        self,
        sentences: List[str],
        role_hints: Optional[List[str]] = None,
        batch_size: int = 16
    ) -> List[ClassificationResult]:
        """
        Classify multiple sentences in batches for efficiency.

        Args:
            sentences: List of sentences to classify
            role_hints: Optional list of role hints for each sentence
            batch_size: Number of sentences per batch

        Returns:
            List of ClassificationResult objects
        """
        self._load_model()

        import torch
        import torch.nn.functional as F

        results = []

        for i in range(0, len(sentences), batch_size):
            batch_sentences = sentences[i:i + batch_size]
            batch_hints = role_hints[i:i + batch_size] if role_hints else [None] * len(batch_sentences)

            # Tokenize batch
            inputs = self._tokenizer(
                batch_sentences,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            # Inference
            with torch.no_grad():
                outputs = self._model(**inputs)
                logits = outputs.logits
                probs = F.softmax(logits, dim=-1)

            # Process each result
            probs_np = probs.cpu().numpy()

            for j, (sentence, prob_row, hint) in enumerate(zip(batch_sentences, probs_np, batch_hints)):
                top_indices = np.argsort(prob_row)[::-1][:3]

                predicted_id = top_indices[0]
                predicted_label = self._id2label.get(predicted_id, f"UNKNOWN_{predicted_id}")
                confidence = float(prob_row[predicted_id])

                top_3 = [
                    (self._id2label.get(idx, f"UNKNOWN_{idx}"), float(prob_row[idx]))
                    for idx in top_indices
                ]

                role = get_label_role(predicted_label)

                # Apply role hint if provided
                if hint and role != hint:
                    role_prefix = "CO-" if hint == "counselor" else "CL-"
                    for idx in top_indices:
                        label = self._id2label.get(idx, "")
                        if label.startswith(role_prefix):
                            predicted_label = label
                            confidence = float(prob_row[idx])
                            role = hint
                            break

                results.append(ClassificationResult(
                    sentence=sentence,
                    label=predicted_label,
                    label_level2=get_label_level2(predicted_label),
                    confidence=confidence,
                    role=role,
                    top_3=top_3
                ))

        return results

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        self._load_sentence_tokenizer()

        if not text or not text.strip():
            return []

        sentences = self._sentence_tokenizer(text)
        # Filter out very short sentences (likely noise)
        return [s.strip() for s in sentences if len(s.strip()) > 3]

    def analyze_message(
        self,
        message_id: int,
        sender: str,
        content: str,
        role_hint: Optional[str] = None
    ) -> MessageAnalysis:
        """
        Analyze a single message.

        Args:
            message_id: ID of the message
            sender: Sender name/identifier
            content: Message content
            role_hint: Optional role hint ('counselor' or 'client')

        Returns:
            MessageAnalysis with sentence-level results
        """
        # Split into sentences
        sentences = self.split_into_sentences(content)

        if not sentences:
            return MessageAnalysis(
                message_id=message_id,
                sender=sender,
                role=role_hint or "unknown",
                sentences=[],
                dominant_label="",
                dominant_label_level2="",
                avg_confidence=0.0
            )

        # Classify all sentences
        role_hints = [role_hint] * len(sentences) if role_hint else None
        results = self.classify_sentences_batch(sentences, role_hints)

        # Compute dominant label
        label_counts = defaultdict(int)
        label_level2_counts = defaultdict(int)
        total_confidence = 0.0

        for r in results:
            label_counts[r.label] += 1
            label_level2_counts[r.label_level2] += 1
            total_confidence += r.confidence

        dominant_label = max(label_counts, key=label_counts.get) if label_counts else ""
        dominant_label_level2 = max(label_level2_counts, key=label_level2_counts.get) if label_level2_counts else ""
        avg_confidence = total_confidence / len(results) if results else 0.0

        # Determine role from results
        role = role_hint
        if not role and results:
            co_count = sum(1 for r in results if r.role == "counselor")
            cl_count = sum(1 for r in results if r.role == "client")
            role = "counselor" if co_count > cl_count else "client"

        return MessageAnalysis(
            message_id=message_id,
            sender=sender,
            role=role or "unknown",
            sentences=results,
            dominant_label=dominant_label,
            dominant_label_level2=dominant_label_level2,
            avg_confidence=avg_confidence
        )

    def analyze_thread(
        self,
        thread_id: int,
        pillar_number: int,
        messages: List[Dict[str, Any]]
    ) -> ThreadAnalysis:
        """
        Analyze a complete email thread.

        Args:
            thread_id: ID of the thread
            pillar_number: Pillar number (1-5)
            messages: List of message dicts with 'id', 'sender', 'content' keys

        Returns:
            ThreadAnalysis with complete results
        """
        message_analyses = []
        all_labels = []
        all_labels_level2 = []

        for msg in messages:
            # Determine role hint from sender
            sender = msg.get('sender', '')
            sender_lower = sender.lower()
            role_hint = None
            if any(term in sender_lower for term in ['berater', 'counsellor', 'counselor', 'assistant', 'bot']):
                role_hint = "counselor"
            elif any(term in sender_lower for term in ['klient', 'client', 'user', 'ratsuchend']):
                role_hint = "client"

            analysis = self.analyze_message(
                message_id=msg.get('id', 0),
                sender=sender,
                content=msg.get('content', ''),
                role_hint=role_hint
            )
            message_analyses.append(analysis)

            # Collect labels
            for sentence in analysis.sentences:
                all_labels.append(sentence.label)
                all_labels_level2.append(sentence.label_level2)

        # Compute distributions
        label_distribution = dict(defaultdict(int))
        label_distribution_level2 = dict(defaultdict(int))

        for label in all_labels:
            label_distribution[label] = label_distribution.get(label, 0) + 1
        for label in all_labels_level2:
            label_distribution_level2[label] = label_distribution_level2.get(label, 0) + 1

        # Compute transition matrix (label -> label transitions)
        transition_matrix = defaultdict(lambda: defaultdict(int))
        for i in range(1, len(all_labels)):
            prev_label = all_labels[i-1]
            curr_label = all_labels[i]
            transition_matrix[prev_label][curr_label] += 1

        # Convert to regular dict for JSON serialization
        transition_matrix_dict = {
            k: dict(v) for k, v in transition_matrix.items()
        }

        # Count by role
        counselor_sentences = sum(1 for label in all_labels if label.startswith("CO-"))
        client_sentences = sum(1 for label in all_labels if label.startswith("CL-"))

        return ThreadAnalysis(
            thread_id=thread_id,
            pillar_number=pillar_number,
            messages=message_analyses,
            label_distribution=label_distribution,
            label_distribution_level2=label_distribution_level2,
            transition_matrix=transition_matrix_dict,
            total_sentences=len(all_labels),
            counselor_sentences=counselor_sentences,
            client_sentences=client_sentences
        )

    def compute_transition_matrix(
        self,
        labels: List[str],
        use_level2: bool = False
    ) -> Tuple[Dict[str, Dict[str, int]], Dict[str, Dict[str, float]]]:
        """
        Compute transition matrix from a sequence of labels.

        Args:
            labels: List of labels in sequence order
            use_level2: If True, aggregate to level 2 labels

        Returns:
            Tuple of (count_matrix, probability_matrix)
        """
        if use_level2:
            labels = [get_label_level2(l) for l in labels]

        # Count transitions
        counts = defaultdict(lambda: defaultdict(int))
        for i in range(1, len(labels)):
            prev_label = labels[i-1]
            curr_label = labels[i]
            counts[prev_label][curr_label] += 1

        # Compute probabilities
        probs = defaultdict(lambda: defaultdict(float))
        for from_label, transitions in counts.items():
            total = sum(transitions.values())
            for to_label, count in transitions.items():
                probs[from_label][to_label] = count / total if total > 0 else 0

        return dict({k: dict(v) for k, v in counts.items()}), dict({k: dict(v) for k, v in probs.items()})

    def compute_impact_factor_ratio(self, label_distribution: Dict[str, int]) -> float:
        """
        Compute the Impact Factor ratio for counselor messages.

        Impact Factor labels (CO-IF-*) indicate therapeutic interventions.
        Higher ratio = more active counseling approach.
        """
        if_count = 0
        total_co = 0

        for label, count in label_distribution.items():
            if label.startswith("CO-"):
                total_co += count
                if label.startswith("CO-IF-"):
                    if_count += count

        return if_count / total_co if total_co > 0 else 0

    def compute_resource_activation_score(self, label_distribution: Dict[str, int]) -> float:
        """
        Compute Resource Activation score.

        Measures how much the counselor focuses on activating client resources.
        """
        ra_count = 0
        total_co = 0

        for label, count in label_distribution.items():
            if label.startswith("CO-"):
                total_co += count
                if "RA" in label:  # Resource Activation
                    ra_count += count

        return ra_count / total_co if total_co > 0 else 0

    def compute_mutual_information(
        self,
        transition_matrix: Dict[str, Dict[str, int]]
    ) -> float:
        """
        Compute Mutual Information score from transition matrix.

        Higher MI indicates more predictable conversation patterns.
        """
        import math

        # Count totals
        total = sum(sum(row.values()) for row in transition_matrix.values())
        if total == 0:
            return 0

        # Row sums (P(X))
        row_sums = {label: sum(transitions.values()) for label, transitions in transition_matrix.items()}

        # Column sums (P(Y))
        col_sums = defaultdict(int)
        for transitions in transition_matrix.values():
            for to_label, count in transitions.items():
                col_sums[to_label] += count

        # Compute MI
        mi = 0.0
        for from_label, transitions in transition_matrix.items():
            for to_label, count in transitions.items():
                if count > 0:
                    p_xy = count / total
                    p_x = row_sums[from_label] / total
                    p_y = col_sums[to_label] / total
                    if p_x > 0 and p_y > 0:
                        mi += p_xy * math.log2(p_xy / (p_x * p_y))

        return mi


# Singleton instance
_oncoco_service: Optional[OnCoCoService] = None


def get_oncoco_service(model_path: Optional[str] = None) -> OnCoCoService:
    """Get or create the OnCoCo service singleton."""
    global _oncoco_service

    if _oncoco_service is None or model_path:
        _oncoco_service = OnCoCoService(model_path)

    return _oncoco_service
