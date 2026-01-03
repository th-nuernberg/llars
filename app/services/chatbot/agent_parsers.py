# agent_parsers.py
"""
Agent Response Parsing Module.

Provides parsing utilities for agent chat responses (ACT, ReAct, ReflAct).
Handles extraction of THOUGHT, ACTION, REFLECTION, FINAL ANSWER patterns.
"""

import re
from typing import Tuple, Optional, List


def parse_action(text: str) -> Tuple[str, str]:
    """
    Parse ACTION: tool(param) format.

    Args:
        text: Response text to parse

    Returns:
        Tuple of (action_name, parameter)
    """
    # Match patterns like: ACTION: tool_name(parameter) or ACTION: tool_name("parameter")
    patterns = [
        r'ACTION:\s*(\w+)\s*\(\s*["\']?(.+?)["\']?\s*\)',
        r'ACTION:\s*(\w+)\s*\(\s*\)',
        r'ACTION:\s*(\w+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            action = match.group(1).lower()
            param = match.group(2) if len(match.groups()) > 1 else ""
            return action, param.strip() if param else ""

    return "respond", text


def normalize_action_from_tool_call(
    action: str,
    param: str,
    action_text: str,
    enabled_tools: Optional[List[str]] = None
) -> Tuple[str, str]:
    """
    Convert embedded tool-call strings into proper actions.

    Args:
        action: Parsed action name
        param: Parsed parameter
        action_text: Original action text
        enabled_tools: List of enabled tool names

    Returns:
        Tuple of (normalized_action, normalized_param)
    """
    if action == "respond" or (enabled_tools and action not in enabled_tools):
        embedded_action, embedded_param = parse_embedded_tool_call(param, enabled_tools)
        if not embedded_action:
            embedded_action, embedded_param = parse_embedded_tool_call(action_text, enabled_tools)
        if embedded_action:
            return embedded_action, embedded_param
    return action, param


def parse_embedded_tool_call(
    text: Optional[str],
    enabled_tools: Optional[List[str]] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract tool calls from wrapper formats like [TOOL_CALLS]rag_search("q").

    Args:
        text: Text that may contain embedded tool calls
        enabled_tools: List of enabled tool names for validation

    Returns:
        Tuple of (action, param) or (None, None) if not found
    """
    if not text:
        return None, None

    candidate = text.strip()
    patterns = [
        (r'\[TOOL_CALLS\]\s*(\w+)\s*\(\s*["\']?(.+?)["\']?\s*\)', False),
        (r'\[TOOL_CALLS\]\s*(\w+)\s*\(\s*\)', False),
        (r'\bTOOL_CALLS\b\s*:?\s*(\w+)\s*\(\s*["\']?(.+?)["\']?\s*\)', False),
        (r'\bTOOL_CALLS\b\s*:?\s*(\w+)\s*\(\s*\)', False),
        (r'^\s*(\w+)\s*\(\s*["\']?(.+?)["\']?\s*\)\s*$', True),
        (r'^\s*(\w+)\s*\(\s*\)\s*$', True),
    ]

    for pattern, enforce_enabled in patterns:
        match = re.search(pattern, candidate, re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        action = match.group(1).lower()
        param = match.group(2) if len(match.groups()) > 1 else ""
        if enforce_enabled and enabled_tools and action not in enabled_tools:
            continue
        return action, (param or "").strip()

    return None, None


def parse_react_response(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse ReAct response for THOUGHT, ACTION, FINAL ANSWER.

    Args:
        text: LLM response text

    Returns:
        Tuple of (thought, action, final_answer)
    """
    thought = None
    action = None
    final_answer = None

    # Extract THOUGHT
    thought_match = re.search(
        r'THOUGHT:\s*(.+?)(?=ACTION:|FINAL ANSWER:|$)',
        text, re.IGNORECASE | re.DOTALL
    )
    if thought_match:
        thought = thought_match.group(1).strip()

    # Extract ACTION
    action_match = re.search(
        r'ACTION:\s*(.+?)(?=OBSERVATION:|FINAL ANSWER:|$)',
        text, re.IGNORECASE | re.DOTALL
    )
    if action_match:
        action = action_match.group(1).strip()

    # Extract FINAL ANSWER
    final_match = re.search(
        r'FINAL ANSWER:\s*(.+?)$',
        text, re.IGNORECASE | re.DOTALL
    )
    if final_match:
        final_answer = final_match.group(1).strip()

    return thought, action, final_answer


def parse_reflact_response(
    text: str
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Parse ReflAct response for REFLECTION, THOUGHT, ACTION, FINAL ANSWER.

    Legacy version that supports THOUGHT as separate step.

    Args:
        text: LLM response text

    Returns:
        Tuple of (reflection, thought, action, final_answer)
    """
    reflection = None
    thought = None
    action = None
    final_answer = None

    # Extract REFLECTION
    reflection_match = re.search(
        r'REFLECTION:\s*(.+?)(?=THOUGHT:|ACTION:|FINAL ANSWER:|$)',
        text, re.IGNORECASE | re.DOTALL
    )
    if reflection_match:
        reflection = reflection_match.group(1).strip()

    # Extract THOUGHT
    thought_match = re.search(
        r'THOUGHT:\s*(.+?)(?=ACTION:|FINAL ANSWER:|$)',
        text, re.IGNORECASE | re.DOTALL
    )
    if thought_match:
        thought = thought_match.group(1).strip()

    # Extract ACTION
    action_match = re.search(
        r'ACTION:\s*(.+?)(?=OBSERVATION:|FINAL ANSWER:|$)',
        text, re.IGNORECASE | re.DOTALL
    )
    if action_match:
        action = action_match.group(1).strip()

    # Extract FINAL ANSWER
    final_match = re.search(
        r'FINAL ANSWER:\s*(.+?)$',
        text, re.IGNORECASE | re.DOTALL
    )
    if final_match:
        final_answer = final_match.group(1).strip()

    return reflection, thought, action, final_answer


def parse_reflact_response_v2(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse ReflAct response for REFLECTION, ACTION, FINAL ANSWER.

    Based on the ReflAct paper - NO separate THOUGHT step.
    The reflection IS the thinking, grounded in state relative to goal.

    Args:
        text: LLM response text

    Returns:
        Tuple of (reflection, action, final_answer)
    """
    reflection = None
    action = None
    final_answer = None

    # Extract REFLECTION - everything until ACTION or FINAL ANSWER
    reflection_match = re.search(
        r'REFLECTION:\s*(.+?)(?=ACTION:|FINAL ANSWER:|THOUGHT:|GOAL:|$)',
        text, re.IGNORECASE | re.DOTALL
    )
    if reflection_match:
        reflection = reflection_match.group(1).strip()
    else:
        # Backwards-compatible: accept legacy THOUGHT label as reflection.
        thought_match = re.search(
            r'THOUGHT:\s*(.+?)(?=ACTION:|FINAL ANSWER:|REFLECTION:|GOAL:|$)',
            text, re.IGNORECASE | re.DOTALL
        )
        if thought_match:
            reflection = thought_match.group(1).strip()

    # Extract ACTION
    action_match = re.search(
        r'ACTION:\s*(.+?)(?=OBSERVATION:|REFLECTION:|FINAL ANSWER:|THOUGHT:|GOAL:|$)',
        text, re.IGNORECASE | re.DOTALL
    )
    if action_match:
        action = action_match.group(1).strip()

    # Extract FINAL ANSWER
    final_match = re.search(
        r'FINAL ANSWER:\s*(.+?)(?=ACTION:|REFLECTION:|THOUGHT:|GOAL:|$)',
        text, re.IGNORECASE | re.DOTALL
    )
    if final_match:
        final_answer = final_match.group(1).strip()

    return reflection, action, final_answer


def strip_trailing_reflact_fragment(text: Optional[str]) -> Optional[str]:
    """
    Remove stray ACTION fragments that leak into ReflAct output/streaming.

    Args:
        text: Text that may have trailing fragments

    Returns:
        Cleaned text
    """
    if not text:
        return text

    cleaned = text.rstrip()
    cleaned = re.sub(
        r'(?m)\n\s*(?:A|AC|ACT|ACTI|ACTIO|ACTION)\s*:?\s*$',
        '',
        cleaned
    ).rstrip()
    cleaned = re.sub(
        r'(?m)\s+(?:ACTION|ACTIO|ACTI|ACT|CTION)\s*:?\s*$',
        '',
        cleaned
    ).rstrip()
    return cleaned


def extract_goal(text: str, allow_partial: bool = False) -> str:
    """
    Extract GOAL from response.

    Args:
        text: The LLM response text
        allow_partial: If True, return partial text even without GOAL: prefix (for streaming).
                       If False, only return text if GOAL: pattern is found.

    Returns:
        Extracted goal text
    """
    if not text:
        return ""

    # Try to match GOAL: pattern
    goal_match = re.search(
        r'GOAL:\s*(.+?)(?=REFLECTION:|THOUGHT:|ACTION:|$)',
        text, re.IGNORECASE | re.DOTALL
    )
    if goal_match:
        return goal_match.group(1).strip()

    # For streaming: only return partial if it looks like a valid goal start
    if allow_partial:
        simple_match = re.search(r'GOAL:\s*(.+)', text, re.IGNORECASE | re.DOTALL)
        if simple_match:
            return simple_match.group(1).strip()

    # For final extraction: fallback to cleaned text
    if not allow_partial:
        cleaned = re.sub(r'^G?O?A?L?:?\s*', '', text.strip(), flags=re.IGNORECASE)
        return cleaned[:200] if cleaned else ""

    return ""
