import csv
import os
import re
from pathlib import Path
from typing import List, Dict, Optional

from aihandler import generate_with_llama, llama_available, read_text_safe
from overview import _collect_repo_text, _compute_repo_metadata
import config


def _create_test_scenario_prompt(repo_text: str, repo_metadata: Dict[str, str]) -> str:
    """Create a prompt for generating test scenarios."""
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


def _create_code_template_prompt(repo_text: str, repo_metadata: Dict[str, str]) -> str:
    """Create a prompt for generating test code templates."""
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
        repo_text = _collect_repo_text(repo_folder_path)
        repo_metadata = _compute_repo_metadata(repo_folder_path)
        
        prompt = _create_test_scenario_prompt(repo_text, repo_metadata)
        result = generate_with_llama(prompt, max_tokens=config.TEST_MAX_TOKENS)
        
        return result
    except Exception as e:
        print(f"Error generating test scenarios: {e}")
        return None


def generate_code_templates(repo_folder_path: str) -> Optional[str]:
    """
    Generate test code templates for a repository using AI.
    Returns the raw AI-generated text.
    """
    if not llama_available():
        return None

    try:
        repo_text = _collect_repo_text(repo_folder_path)
        repo_metadata = _compute_repo_metadata(repo_folder_path)
        
        prompt = _create_code_template_prompt(repo_text, repo_metadata)
        result = generate_with_llama(prompt, max_tokens=config.TEST_MAX_TOKENS)
        
        return result
    except Exception as e:
        print(f"Error generating code templates: {e}")
        return None


def parse_ai_output_to_csv(ai_text: str) -> List[Dict[str, str]]:
    """
    Parse AI-generated text into structured test data.
    Expects format with TEST ID, TEST NAME, DESCRIPTION, EXPECTED RESULT blocks.
    Returns list of dictionaries with keys: test_id, test_name, description, expected_result
    """
    tests: List[Dict[str, str]] = []
    
    if not ai_text:
        return tests
    
    # Split by test blocks (look for TEST ID pattern)
    pattern = r'TEST\s+ID:\s*(\d+)\s*\n\s*TEST\s+NAME:\s*([^\n]+)\s*\n\s*DESCRIPTION:\s*([^\n]+)\s*\n\s*EXPECTED\s+RESULT:\s*([^\n]+)'
    
    matches = re.findall(pattern, ai_text, re.IGNORECASE)
    
    for match in matches:
        test_id, test_name, description, expected_result = match
        tests.append({
            'test_id': test_id.strip(),
            'test_name': test_name.strip(),
            'description': description.strip(),
            'expected_result': expected_result.strip()
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
        print(f"Error writing CSV: {e}")
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
        print(f"Error listing test sets: {e}")
    
    return test_files
