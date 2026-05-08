# Option 2 - Integrating AI into explaining code, through files or libraries.

from pathlib import Path
import os
from typing import List, Set, Dict, Tuple, Optional
from collections import defaultdict
import re

from aihandler import generate_with_llama, llama_available, read_text_safe
from overview import SKIP_DIRS
import config

MAX_SNIPPETS = 5


# Focus ONLY on actual programming languages (not config/text)
CODE_EXTENSIONS: Set[str] = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".go", ".rs", ".rb", ".php",
    ".swift", ".kt", ".kts",
}

def collect_code_file_paths(repo_folder_path: str) -> List[str]: # Returns list of code file paths relative to repo root
    repo_root = Path(repo_folder_path)
    if not repo_root.exists() or not repo_root.is_dir():
        return []

    code_files: List[str] = []

    for root, dirs, files in os.walk(repo_root):
        # Mutate dirs in-place to skip unwanted folders
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS] # Only adds if not in skip list

        for file_name in files:
            file_path = Path(root) / file_name

            if file_path.suffix.lower() in CODE_EXTENSIONS:
                try:
                    relative_path = file_path.relative_to(repo_root)
                    code_files.append(str(relative_path))
                except Exception:
                    continue

    return sorted(code_files)

def collect_code_files_by_language(repo_folder_path: str) -> Dict[str, List[str]]: # Returns a dict of files by extension
    files = collect_code_file_paths(repo_folder_path)
    grouped: Dict[str, List[str]] = defaultdict(list)
    for path in files:
        ext = Path(path).suffix.lower()
        grouped[ext].append(path)

    return dict(grouped)


# Supported languages (expand later if needed)
PYTHON_EXTENSIONS = {".py"}
JS_EXTENSIONS = {".js", ".ts", ".jsx", ".tsx"}

# ------------------------
# EXTRACTORS
# ------------------------

def _extract_python_imports(content: str) -> Set[str]:
    imports = set()

    # import x.y
    imports.update(re.findall(r'^\s*import\s+([\w\.]+)', content, re.MULTILINE))

    # from x.y import z
    imports.update(re.findall(r'^\s*from\s+([\w\.]+)\s+import', content, re.MULTILINE))

    return imports


def _extract_js_imports(content: str) -> Set[str]:
    imports = set()

    # import ... from 'module'
    imports.update(re.findall(r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]', content))

    # require('module')
    imports.update(re.findall(r'require\([\'"](.+?)[\'"]\)', content))

    return imports


# ------------------------
# PATH RESOLVERS
# ------------------------

def _resolve_python_import(base_path: Path, repo_root: Path, module: str) -> List[Path]:
    """
    Convert 'utils.helpers' -> repo_root/utils/helpers.py
    """
    parts = module.split(".")
    possible_paths = []

    # file.py
    file_path = repo_root.joinpath(*parts).with_suffix(".py")
    possible_paths.append(file_path)

    # package/__init__.py
    init_path = repo_root.joinpath(*parts, "__init__.py")
    possible_paths.append(init_path)

    return [p for p in possible_paths if p.exists()]


def _resolve_js_import(base_path: Path, repo_root: Path, module: str) -> List[Path]:
    """
    Resolve relative imports like './utils'
    Ignore external packages like 'react'
    """
    if not module.startswith("."):
        return []  # skip node_modules

    base_dir = base_path.parent
    target = (base_dir / module).resolve()

    candidates = [
        target.with_suffix(ext) for ext in JS_EXTENSIONS
    ] + [
        target / "index.js",
        target / "index.ts"
    ]

    return [p for p in candidates if p.exists()]


# ------------------------
# MAIN WALKER
# ------------------------

def resolve_dependencies( # Given a file, find related files through imports (up to a certain depth)
    file_path: str,
    repo_root: str,
    max_depth: int = 2
) -> List[str]:
    repo_root_path = Path(repo_root).resolve()
    start_path = Path(file_path).resolve()

    visited: Set[Path] = set()
    results: Set[tuple[Path, int]] = set()

    def _walk(current_path: Path, depth: int):
        if depth > max_depth or current_path in visited:
            return

        visited.add(current_path)

        try:
            content = current_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        ext = current_path.suffix.lower()

        if ext in PYTHON_EXTENSIONS:
            imports = _extract_python_imports(content)
            resolver = _resolve_python_import

        elif ext in JS_EXTENSIONS:
            imports = _extract_js_imports(content)
            resolver = _resolve_js_import

        else:
            return

        for module in imports:
            resolved_paths = resolver(current_path, repo_root_path, module)

            for path in resolved_paths:
                if path.exists():
                    results.add((path, depth + 1))
                    _walk(path, depth + 1)

    _walk(start_path, 0)

    # Convert to relative paths
    return sorted([
        (str(p.relative_to(repo_root_path)), d)
        for (p, d) in results
        if p != start_path
    ], key=lambda x: x[1])  # optional: sort by depth


def get_repo_code_files(repo_folder_path: str) -> List[str]:
    return collect_code_file_paths(repo_folder_path)


_read_file_safe = read_text_safe


def _comment_prefix_for_file(path: Path) -> str:
    extension = path.suffix.lower()
    if extension in {'.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', '.rs', '.kt', '.kts', '.php'}:
        return '//'
    return '#'


def _build_code_explanation_prompt(path: Path, content: str, dependency_snippets: List[str]) -> str:
    prompt = [
        "You are a senior developer helping another engineer understand a code file.",
        "IMPORTANT: Only describe the code provided in this file. Do not invent or reference functions, classes, or imports that are not present in the content below.",
        "Read the file contents below and produce a concise explanation that covers:",
        "1. The file's purpose.",
        "2. Main functions or classes.",
        "3. Inputs and outputs.",
        "4. Dependencies and important imported modules.",
        "5. Any implementation details a future maintainer should know.",
        "",
        f"File name: {path.name}",
        f"File path: {path}",
        "",
        "[FILE CONTENT START]",
        content,
        "[FILE CONTENT END]",
    ]

    if dependency_snippets:
        prompt.extend(["", "Relevant dependency snippets:", "[DEPENDENCIES START]"])
        prompt.extend(dependency_snippets[:3])
        prompt.append("[DEPENDENCIES END]")

    prompt.append("")
    prompt.append("Write the explanation now. Keep it developer-focused and reference actual function names, classes, and imports where possible.")
    return "\n".join(prompt)


def generate_code_explanation(file_path: str, repo_root: str = None) -> str:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return "File not found."

    content = _read_file_safe(path, max_chars=800)
    if not content:
        return "Unable to read file contents."

    repo_root_path = Path(repo_root) if repo_root else path.parent
    if not repo_root_path.exists() or not repo_root_path.is_dir():
        repo_root_path = path.parent

    dependency_snippets: List[str] = []
    try:
        dependencies = resolve_dependencies(file_path, str(repo_root_path), max_depth=2)
        for rel_path, depth in dependencies[:3]:
            dep_path = repo_root_path / rel_path
            snippet = _read_file_safe(dep_path, max_chars=1200)
            if snippet:
                dependency_snippets.append(f"Dependency ({rel_path}):\n{snippet}")
    except Exception:
        dependency_snippets = []

    if llama_available():
        prompt = _build_code_explanation_prompt(path, content, dependency_snippets)
        result = generate_with_llama(prompt, max_tokens=config.EXPLAIN_MAX_TOKENS)
        if result:
            return result

    first_lines = [line.strip() for line in content.splitlines() if line.strip()]
    summary_line = first_lines[0] if first_lines else "No meaningful lines could be extracted from the file."
    return (
        f"Code explanation for {path.name}:\n"
        f"- Top line: {summary_line}\n"
        f"- File size: {path.stat().st_size} bytes\n"
        f"- Path: {path}\n"
        f"- If AI is unavailable, open the file and inspect function/class definitions for the main behavior."
    )


def _extract_code_from_ai_response(response: str, original_content: str) -> str:
    """
    Strip prose and markdown fences from an AI annotation response,
    returning only the code portion.

    Strategy:
    1. If a markdown code fence is present, extract the content inside it.
    2. Otherwise, drop leading/trailing lines that look like prose (i.e. lines
       that appear before the first recognisable code line).
    3. Fall back to the full response if nothing useful is found.
    """
    if not response:
        return response

    # --- Strategy 1: extract from markdown code fence ---
    fence_match = re.search(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
    if fence_match:
        extracted = fence_match.group(1).rstrip()
        if extracted:
            return extracted

    # --- Strategy 2: drop leading/trailing prose lines ---
    # A line is considered "code-like" if it starts with a known code pattern.
    code_start_patterns = re.compile(
        r'^\s*('
        r'#|//|/\*|\*'           # comments
        r'|import |from |require'  # imports
        r'|def |class |function |const |let |var |public |private |protected '
        r'|return |if |for |while |try |async |export '
        r'|@'                    # decorators / annotations
        r'|\w+\s*[=({]'         # assignments / calls
        r')'
    )

    lines = response.splitlines()
    first_code = None
    last_code = None
    for i, line in enumerate(lines):
        if code_start_patterns.match(line) or (line.strip() == '' and first_code is not None):
            if first_code is None:
                first_code = i
            last_code = i

    if first_code is not None:
        # Trim trailing blank lines
        trimmed = lines[first_code:last_code + 1]
        while trimmed and not trimmed[-1].strip():
            trimmed.pop()
        result = '\n'.join(trimmed)
        if result:
            return result

    # --- Fallback: return the full response unchanged ---
    return response


def _build_annotation_prompt(path: Path, content: str) -> str:
    comment_prefix = _comment_prefix_for_file(path)
    return "\n".join([
        "You are adding comments to functions in a code file to explain their behaviour",
        "Preserve the original code exactly and do not change its behavior.",
        f"Use {comment_prefix} as the comment syntax for this file.",
        "Return only the rewritten source code with comments included.",
        "",
        f"File name: {path.name}",
        "",
        "Source code:",
        "---",
        content,
        "---",
    ])


def annotate_code_file(file_path: str, repo_root: str = None) -> str:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return "File not found."

    content = _read_file_safe(path, max_chars=14000)
    if not content:
        return "Unable to read file contents."

    if llama_available():
        prompt = _build_annotation_prompt(path, content)
        # Output must be at least 1.5× the input length to fit the annotated code.
        # Use ~3 chars per token as a conservative estimate for source code.
        dynamic_max_tokens = max(config.EXPLAIN_MAX_TOKENS, int(len(content) * 1.5 / 3))
        result = generate_with_llama(prompt, max_tokens=dynamic_max_tokens)
        if result:
            return _extract_code_from_ai_response(result, content)

    comment_char = _comment_prefix_for_file(path)
    annotated_lines: List[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("def ") or stripped.startswith("class "):
            annotated_lines.append(f"{comment_char} Explain: {stripped}")
        annotated_lines.append(line)

    return "\n".join(annotated_lines)


def save_annotated_file(file_path: str, annotated_content: str, target_path: str = None) -> tuple[bool, str]:
    source_path = Path(file_path)
    if not source_path.exists() or not source_path.is_file():
        return False, "Original file not found."

    if not annotated_content:
        return False, "No annotated content provided."

    if target_path:
        target = Path(target_path)
    else:
        target = source_path.with_suffix(source_path.suffix + ".annotated")

    try:
        target.write_text(annotated_content, encoding="utf-8")
        return True, str(target)
    except Exception as exc:
        return False, str(exc)


def _score_dependency(
    file_content: str,
    import_name: str,
    dependency_path: Path,
    depth: int
) -> float:
    score = 0.0

    # 1. Direct usage boost
    if import_name:
        usage_count = len(re.findall(rf'\b{re.escape(import_name.split(".")[-1])}\b', file_content))
        score += min(usage_count * 2, 10)

    # 2. Depth penalty
    score -= depth * 2

    # 3. Smaller file boost (prefer concise utilities)
    try:
        size_kb = dependency_path.stat().st_size / 1024
        if size_kb < 10:
            score += 3
        elif size_kb > 100:
            score -= 2
    except Exception:
        pass

    return score


def build_context(
    primary_file: str,
    repo_root: str,
    dependencies_with_depth: List[Tuple[str, int]],
) -> str:
    """
    dependencies_with_depth = [(relative_path, depth), ...]
    """

    repo_root_path = Path(repo_root)
    primary_path = Path(primary_file)

    primary_content = _read_file_safe(primary_path, max_chars=6000)

    scored = []

    for dep_path_str, depth in dependencies_with_depth:
        dep_path = repo_root_path / dep_path_str
        import_name = Path(dep_path_str).stem

        score = _score_dependency(
            primary_content,
            import_name,
            dep_path,
            depth
        )

        scored.append((score, dep_path))

    # Sort by relevance
    scored.sort(key=lambda x: x[0], reverse=True)

    # Take top N
    selected = scored[:MAX_SNIPPETS]

    snippets = []

    for score, path in selected:
        content = _read_file_safe(path)
        if content:
            rel = path.relative_to(repo_root_path)
            snippets.append(f"Dependency ({rel}):\n{content}")

    return (
        f"PRIMARY FILE:\n{primary_content}\n\n"
        + "\n\n---\n\n".join(snippets)
    )