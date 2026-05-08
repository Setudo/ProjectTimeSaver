import csv
import os
import re
from pathlib import Path
from typing import List, Dict, Optional

from aihandler import generate_with_llama, llama_available, read_text_safe, get_model_context_budget
from overview import _collect_repo_text, _compute_repo_metadata
import config
from logger import AppLogger

logger = AppLogger(os.path.dirname(__file__))

# Max tokens reserved for the model's response when running on a small-context model.
# Prompt + response must fit within the model's n_ctx (2048 for TinyLlama).
# TinyLlama: n_ctx=2048, compact prompt capped at ~1400 chars (~350 tokens),
# leaving ~600 tokens for the response — 512 is a safe ceiling that fits 3+ blocks.
_SMALL_CTX_MAX_TOKENS = 512


# Character budget reserved for the fixed parts of the compact prompt (labels,
# instructions, metadata).  Repo text is capped to whatever remains.
_COMPACT_PROMPT_OVERHEAD = 300


def _create_test_scenario_prompt(repo_text: str, repo_metadata: Dict[str, str], compact: bool = False) -> str:
    """Create a prompt for generating test scenarios."""
    if compact:
        # Reserve space for instructions so repo text doesn't crowd them out.
        repo_snippet = repo_text[:max(0, 1400 - _COMPACT_PROMPT_OVERHEAD)]
        return (
            f"Folders: {repo_metadata.get('top_level_dirs', '')}\n"
            f"Languages: {repo_metadata.get('language_summary', '')}\n\n"
            f"{repo_snippet}\n\n"
            "List 3 test scenarios. For each write exactly these 4 lines then ---:\n"
            "TEST ID: 1\nTEST NAME: <name>\nDESCRIPTION: <what to test>\nEXPECTED RESULT: <outcome>\n---"
        )
    return f"""Based on the following repository analysis, generate a comprehensive set of test scenarios.

REPOSITORY ANALYSIS:
{repo_text}

REPOSITORY METADATA:
{repo_metadata}

Please generate test scenarios in the following format:
For each test, use the exact format:
TEST ID: <number>
TEST NAME: <name>
DESCRIPTION: <description of what to test>
EXPECTED RESULT: <expected outcome>

---

Generate between 8-15 test scenarios. Be specific and practical. Focus on:
1. Core functionality
2. Edge cases
3. Error handling
4. Integration points

Ensure each test is independent and testable.
"""


def _create_code_template_prompt(repo_text: str, repo_metadata: Dict[str, str], compact: bool = False) -> str:
    """Create a prompt for generating test code templates."""
    if compact:
        repo_snippet = repo_text[:max(0, 1400 - _COMPACT_PROMPT_OVERHEAD)]
        return (
            f"Folders: {repo_metadata.get('top_level_dirs', '')}\n"
            f"Languages: {repo_metadata.get('language_summary', '')}\n\n"
            f"{repo_snippet}\n\n"
            "List 3 test templates. For each write exactly these 4 lines then ---:\n"
            "TEST ID: 1\nTEST NAME: <name>\nDESCRIPTION: <what the test does>\nEXPECTED RESULT: <what should pass>\n---"
        )
    return f"""Based on the following repository analysis, generate test code templates.

REPOSITORY ANALYSIS:
{repo_text}

REPOSITORY METADATA:
{repo_metadata}

Please generate test code templates in the following format:
For each test template, use the exact format:
TEST ID: <number>
TEST NAME: <name>
DESCRIPTION: <description of what the test does>
EXPECTED RESULT: <what should pass>

---

Generate between 8-15 test templates with basic code structure hints. Include:
1. Unit test templates
2. Integration test templates
3. Error case tests

For each template, suggest the programming language and basic assertion pattern.

Ensure templates are framework-agnostic but realistic.
"""


def generate_test_scenarios(repo_folder_path: str) -> Optional[str]:
    """
    Generate test scenarios for a repository using AI.
    Returns the raw AI-generated text.
    """
    if not llama_available():
        return None

    try:
        budget = get_model_context_budget()
        compact = budget <= 2000
        repo_text = _collect_repo_text(repo_folder_path, budget=budget if compact else None)
        repo_metadata = _compute_repo_metadata(repo_folder_path)

        prompt = _create_test_scenario_prompt(repo_text, repo_metadata, compact=compact)
        max_tokens = _SMALL_CTX_MAX_TOKENS if compact else config.TEST_MAX_TOKENS
        result = generate_with_llama(prompt, max_tokens=max_tokens)

        return result
    except Exception as e:
        logger.error(f"Error generating test scenarios: {e}")
        return None


def generate_code_templates(repo_folder_path: str) -> Optional[str]:
    """
    Generate test code templates for a repository using AI.
    Returns the raw AI-generated text.
    """
    if not llama_available():
        return None

    try:
        budget = get_model_context_budget()
        compact = budget <= 2000
        repo_text = _collect_repo_text(repo_folder_path, budget=budget if compact else None)
        repo_metadata = _compute_repo_metadata(repo_folder_path)

        prompt = _create_code_template_prompt(repo_text, repo_metadata, compact=compact)
        max_tokens = _SMALL_CTX_MAX_TOKENS if compact else config.TEST_MAX_TOKENS
        result = generate_with_llama(prompt, max_tokens=max_tokens)

        return result
    except Exception as e:
        logger.error(f"Error generating code templates: {e}")
        return None


def _extract_field(label: str, text: str) -> str:
    """
    Extract the value for a labelled field from a block of text.

    Handles:
    - Optional leading ** (bold markdown)
    - Any amount of whitespace after the colon
    - Case-insensitive matching
    """
    pattern = rf'\*{{0,2}}{re.escape(label)}\*{{0,2}}\s*:\s*(.+)'
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def parse_ai_output_to_csv(ai_text: str) -> List[Dict[str, str]]:
    """
    Parse AI-generated text into structured test data.

    Strategy:
    1. Try a strict consecutive-line regex first (fast path for well-formed output).
    2. Fall back to a block-splitting approach that tolerates blank lines between
       fields and minor formatting variations (bold markers, extra whitespace, etc.).

    Returns list of dicts with keys: test_id, test_name, description, expected_result.
    """
    tests: List[Dict[str, str]] = []

    if not ai_text:
        return tests

    # --- Pass 1: strict pattern (fields on consecutive lines, no blank lines) ---
    strict_pattern = (
        r'TEST\s+ID:\s*(\d+)[^\n]*\n'
        r'[ \t]*\*{0,2}TEST\s+NAME\*{0,2}:\s*([^\n]+)\n'
        r'[ \t]*\*{0,2}DESCRIPTION\*{0,2}:\s*([^\n]+)\n'
        r'[ \t]*\*{0,2}EXPECTED\s+RESULT\*{0,2}:\s*([^\n]+)'
    )
    for m in re.finditer(strict_pattern, ai_text, re.IGNORECASE):
        tests.append({
            'test_id': m.group(1).strip(),
            'test_name': m.group(2).strip(),
            'description': m.group(3).strip(),
            'expected_result': m.group(4).strip(),
        })

    if tests:
        return tests

    # --- Pass 2: block-splitting fallback ---
    # Split on the separator line (---) or on a new TEST ID: line to get per-test chunks.
    # We anchor splits on "TEST ID:" so each chunk starts with that label.
    chunks = re.split(r'(?=\bTEST\s+ID\s*:)', ai_text, flags=re.IGNORECASE)

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        test_id = _extract_field("TEST ID", chunk)
        # Accept only numeric IDs; skip chunks that don't look like a test block.
        if not test_id or not re.match(r'^\d+$', test_id):
            continue

        test_name = _extract_field("TEST NAME", chunk)
        description = _extract_field("DESCRIPTION", chunk)
        expected_result = _extract_field("EXPECTED RESULT", chunk)

        # Require at least a name to consider the block valid.
        if not test_name:
            continue

        tests.append({
            'test_id': test_id,
            'test_name': test_name,
            'description': description,
            'expected_result': expected_result,
        })

    return tests


def create_test_csv(tests: List[Dict[str, str]], output_path: str) -> bool:
    """
    Write test data to a CSV file.
    Returns True if successful, False otherwise.
    """
    if not tests:
        return False
    
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Test ID', 'Test Name', 'Description', 'Expected Result']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for test in tests:
                writer.writerow({
                    'Test ID': test.get('test_id', ''),
                    'Test Name': test.get('test_name', ''),
                    'Description': test.get('description', ''),
                    'Expected Result': test.get('expected_result', '')
                })
        
        return True
    except Exception as e:
        logger.error(f"Error writing CSV: {e}")
        return False


def read_test_csv(file_path: str) -> str:
    """
    Read a CSV file and return formatted text for preview.
    """
    if not os.path.isfile(file_path):
        return "File not found."
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {e}"


def get_next_test_set_number(test_sets_folder: str) -> int:
    """
    Get the next available test set number.
    Looks at existing files and returns the next sequential number.
    """
    if not os.path.isdir(test_sets_folder):
        return 1
    
    existing_numbers = []
    for filename in os.listdir(test_sets_folder):
        if filename.endswith('.csv'):
            match = re.match(r'(\d+)_', filename)
            if match:
                try:
                    num = int(match.group(1))
                    existing_numbers.append(num)
                except ValueError:
                    pass
    
    if not existing_numbers:
        return 1
    
    return max(existing_numbers) + 1


def get_test_sets_list(test_sets_folder: str) -> List[tuple]:
    """
    Get list of all test set CSV files.
    Returns list of tuples: (filename, full_path, file_size, modified_time)
    """
    test_files = []
    
    if not os.path.isdir(test_sets_folder):
        return test_files
    
    try:
        for filename in sorted(os.listdir(test_sets_folder)):
            if filename.endswith('.csv'):
                full_path = os.path.join(test_sets_folder, filename)
                try:
                    file_size = os.path.getsize(full_path)
                    mod_time = os.path.getmtime(full_path)
                    test_files.append((filename, full_path, file_size, mod_time))
                except OSError:
                    pass
    except Exception as e:
        logger.error(f"Error listing test sets: {e}")
    
    return test_files
