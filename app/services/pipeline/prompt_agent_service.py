"""
Prompt Agent Service.

Generates and refines prompt variants for the pipeline using a meta-LLM call.
Uses existing LLMClientFactory for model routing.
"""

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PromptAgentService:
    """Generates prompt variants based on task spec and iteration history."""

    @classmethod
    def generate_variants(
        cls,
        run: Any,
        history: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate prompt variants for the current iteration.

        For the first iteration, generates initial prompts from the task spec.
        For subsequent iterations, refines based on previous scores.

        Args:
            run: PipelineRun instance
            history: List of previous iteration results

        Returns:
            List of prompt variant dicts with keys:
            - template_id (optional): existing PromptTemplate ID
            - variant_name: human-readable name
            - system_prompt: system prompt text
            - user_prompt_template: user prompt template with {content} placeholder
        """
        config = run.config_json or {}
        task_spec = config.get('task_spec', '')
        meta_model = config.get('meta_model_id')
        num_variants = config.get('num_prompt_variants', 3)

        if not history:
            return cls._generate_initial_prompts(
                task_spec=task_spec,
                model_id=meta_model,
                num_variants=num_variants,
                scenario_type=run.scenario_type,
                reference_model_id=run.reference_model_id,
            )
        else:
            return cls._refine_prompts(
                task_spec=task_spec,
                history=history,
                model_id=meta_model,
                num_variants=num_variants,
            )

    @classmethod
    def _generate_initial_prompts(
        cls,
        task_spec: str,
        model_id: Optional[str],
        num_variants: int = 3,
        scenario_type: str = 'greenfield',
        reference_model_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate initial prompt variants from task specification."""
        system_prompt = (
            "You are a prompt engineering expert. Generate diverse prompt variants "
            "for an LLM task. Each variant should take a different approach to achieve "
            "the task goal. Output ONLY valid JSON array."
        )

        user_prompt = cls._build_initial_prompt(
            task_spec, num_variants, scenario_type, reference_model_id
        )

        try:
            response_text = cls._call_llm(model_id, system_prompt, user_prompt)
            variants = cls._parse_variants(response_text, num_variants)
            if variants:
                return variants
        except Exception as e:
            logger.warning("[PromptAgent] LLM call failed, using fallback: %s", e)

        # Fallback: generate simple variants from task spec
        return cls._fallback_variants(task_spec, num_variants)

    @classmethod
    def _refine_prompts(
        cls,
        task_spec: str,
        history: List[Dict[str, Any]],
        model_id: Optional[str],
        num_variants: int = 2,
    ) -> List[Dict[str, Any]]:
        """Refine prompts based on previous iteration results."""
        system_prompt = (
            "You are a prompt engineering expert analyzing evaluation results. "
            "Based on previous iterations and their scores, generate improved prompt "
            "variants that address identified weaknesses. "
            "Do NOT repeat approaches that showed no improvement. "
            "Output ONLY valid JSON array."
        )

        user_prompt = cls._build_refinement_prompt(task_spec, history, num_variants)

        try:
            response_text = cls._call_llm(model_id, system_prompt, user_prompt)
            variants = cls._parse_variants(response_text, num_variants)
            if variants:
                return variants
        except Exception as e:
            logger.warning("[PromptAgent] Refinement LLM call failed: %s", e)

        return cls._fallback_variants(task_spec, num_variants)

    @classmethod
    def _build_initial_prompt(
        cls,
        task_spec: str,
        num_variants: int,
        scenario_type: str,
        reference_model_id: Optional[str],
    ) -> str:
        """Build the prompt for initial variant generation."""
        parts = [
            f"Task Specification:\n{task_spec}\n",
            f"Scenario Type: {scenario_type}",
        ]

        if reference_model_id:
            parts.append(
                f"Reference Model: {reference_model_id} "
                "(analyze and maintain its style characteristics)"
            )

        parts.append(
            f"\nGenerate {num_variants} diverse prompt variants as a JSON array. "
            "Each variant must have:\n"
            '- "variant_name": short descriptive name\n'
            '- "system_prompt": the system prompt\n'
            '- "user_prompt_template": the user message template '
            '(use {content} as placeholder for input text)\n'
            "\nVariants should differ in approach: e.g., structured vs. "
            "conversational, formal vs. empathetic, brief vs. detailed."
        )

        return "\n".join(parts)

    @classmethod
    def _build_refinement_prompt(
        cls,
        task_spec: str,
        history: List[Dict[str, Any]],
        num_variants: int,
    ) -> str:
        """Build the prompt for refinement based on history."""
        parts = [
            f"Task Specification:\n{task_spec}\n",
            "Previous Iterations:",
        ]

        for h in history[-5:]:  # Last 5 iterations max
            parts.append(
                f"\n--- Iteration {h['iteration']} ---\n"
                f"Scores: {json.dumps(h.get('scores', {}))}\n"
                f"Agent Assessment: {h.get('reasoning', 'N/A')}\n"
                f"Prompts Used: {json.dumps(h.get('prompt_variants', []))}"
            )

        # Identify weak dimensions
        if history:
            latest = history[-1].get('scores', {})
            dims = latest.get('dimensions', {})
            weak = [d for d, s in dims.items() if s < 3.5]
            if weak:
                parts.append(f"\nWeak Dimensions to Improve: {', '.join(weak)}")

        parts.append(
            f"\nGenerate {num_variants} REFINED prompt variants that address "
            "the identified weaknesses. Output as JSON array with keys: "
            "variant_name, system_prompt, user_prompt_template. "
            "Do NOT repeat approaches that already failed."
        )

        return "\n".join(parts)

    @classmethod
    def _call_llm(
        cls,
        model_id: Optional[str],
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Make an LLM call using LLMClientFactory."""
        from services.llm.llm_client_factory import LLMClientFactory
        from services.llm.llm_execution_service import LLMExecutionService

        client, api_model = LLMClientFactory.resolve_client_and_model_id(model_id)
        if not client:
            raise RuntimeError(f"Could not resolve model: {model_id}")

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]

        response = LLMExecutionService.execute_chat_completion(
            client,
            model=api_model,
            messages=messages,
            temperature=0.8,
            max_tokens=4000,
        )

        return response.choices[0].message.content

    @classmethod
    def _parse_variants(
        cls,
        response_text: str,
        expected_count: int,
    ) -> Optional[List[Dict[str, Any]]]:
        """Parse LLM response into prompt variants."""
        # Try to find JSON array in response
        text = response_text.strip()

        # Strip markdown code block if present
        if text.startswith('```'):
            lines = text.split('\n')
            # Remove first and last lines (```json and ```)
            lines = [l for l in lines if not l.strip().startswith('```')]
            text = '\n'.join(lines).strip()

        try:
            variants = json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON array from text
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                try:
                    variants = json.loads(text[start:end])
                except json.JSONDecodeError:
                    logger.warning("[PromptAgent] Could not parse JSON from response")
                    return None
            else:
                return None

        if not isinstance(variants, list):
            return None

        # Validate and normalize
        result = []
        for i, v in enumerate(variants[:expected_count]):
            if not isinstance(v, dict):
                continue
            result.append({
                'variant_name': v.get('variant_name', f'Variant {i + 1}'),
                'system_prompt': v.get('system_prompt', ''),
                'user_prompt_template': v.get('user_prompt_template', '{content}'),
            })

        return result if result else None

    @classmethod
    def _fallback_variants(
        cls,
        task_spec: str,
        num_variants: int,
    ) -> List[Dict[str, Any]]:
        """Generate simple fallback variants when LLM call fails."""
        base_variants = [
            {
                'variant_name': 'Standard',
                'system_prompt': f'You are a helpful assistant. {task_spec}',
                'user_prompt_template': 'Please process the following:\n\n{content}',
            },
            {
                'variant_name': 'Structured',
                'system_prompt': (
                    f'You are a precise assistant that produces structured output. {task_spec}'
                ),
                'user_prompt_template': (
                    'Analyze the following input and provide a structured response:\n\n{content}'
                ),
            },
            {
                'variant_name': 'Detailed',
                'system_prompt': (
                    f'You are a thorough assistant. Provide detailed, comprehensive responses. {task_spec}'
                ),
                'user_prompt_template': (
                    'Please provide a detailed analysis of the following:\n\n{content}'
                ),
            },
        ]
        return base_variants[:num_variants]
