import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from aihandler import generate_with_llama, llama_available, read_text_safe
import config
README_CANDIDATES = ["README.md", "README.rst", "README.txt", "README"]
COMMON_TEXT_EXTENSIONS = {".md", ".rst", ".txt", ".py", ".js", ".json", ".yaml", ".yml", ".ini", ".cfg", ".toml"}
ENTRY_POINT_NAMES = {
    "main.py", "app.py", "cli.py", "run.py", "server.py",
    "index.js", "index.ts", "main.go", "main.rs", "main.c", "main.cpp",
}
DEPENDENCY_FILES = ["requirements.txt", "pyproject.toml", "package.json", "go.mod", "Cargo.toml"]
SKIP_DIRS = {"test", "tests", "migrations", "node_modules", ".git", "dist", "build", "__pycache__", ".venv", "venv"}


def _read_file_snippet(path: Path, max_chars: int = 14000) -> str:
    return read_text_safe(path, max_chars=max_chars).strip()


def _collect_repo_text(repo_folder_path: str) -> str:
    repo_folder = Path(repo_folder_path)
    snippets: List[str] = []

    # 1. README — high-level intent
    for readme_name in README_CANDIDATES:
        readme_path = repo_folder / readme_name
        if readme_path.exists():
            content = _read_file_snippet(readme_path, max_chars=4000)
            if content:
                snippets.append(f"README ({readme_name}):\n{content}")
            break

    # 2. Dependency manifest — reveals frameworks and libraries in use
    for dep_file in DEPENDENCY_FILES:
        dep_path = repo_folder / dep_file
        if dep_path.exists():
            snippet = _read_file_snippet(dep_path, max_chars=1000)
            if snippet:
                snippets.append(f"Dependencies ({dep_file}):\n{snippet}")
            break

    # 3. Entry points anywhere in the repo — highest signal for understanding flow
    entry_point_snippets: List[str] = []
    for root, dirs, files in os.walk(repo_folder_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for file_name in files:
            if file_name.lower() in ENTRY_POINT_NAMES:
                file_path = Path(root) / file_name
                snippet = _read_file_snippet(file_path, max_chars=2000)
                if snippet:
                    rel = file_path.relative_to(repo_folder)
                    entry_point_snippets.append(f"Entry point ({rel}):\n{snippet}")
            if len(entry_point_snippets) >= 3:
                break
        if len(entry_point_snippets) >= 3:
            break
    snippets.extend(entry_point_snippets)

    # 4. Remaining source files, skipping tests/build artifacts
    source_files: List[Path] = []
    for root, dirs, files in os.walk(repo_folder_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for file_name in files:
            p = Path(root) / file_name
            if p.suffix.lower() in COMMON_TEXT_EXTENSIONS:
                # Skip files already added as entry points
                if file_name.lower() not in ENTRY_POINT_NAMES:
                    source_files.append(p)

    for file_path in source_files:
        if len(snippets) >= 8:
            break
        snippet = _read_file_snippet(file_path, max_chars=1500)
        if snippet:
            rel = file_path.relative_to(repo_folder)
            snippets.append(f"File ({rel}):\n{snippet}")

    return "\n\n---\n\n".join(snippets) if snippets else "No readable files found."


def _compute_repo_metadata(repo_folder_path: str) -> Dict[str, str]:
    repo_folder = Path(repo_folder_path)
    extension_counts: Dict[str, int] = {}
    top_level_dirs: List[str] = []

    for child in sorted(repo_folder.iterdir()):
        if child.is_dir():
            top_level_dirs.append(child.name)

    for root, _, files in os.walk(repo_folder_path):
        for file_name in files:
            ext = Path(file_name).suffix.lower()
            if ext:
                extension_counts[ext] = extension_counts.get(ext, 0) + 1

    language_names = []
    extension_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".java": "Java",
        ".c": "C",
        ".cpp": "C++",
        ".cs": "C#",
        ".go": "Go",
        ".rs": "Rust",
        ".md": "Markdown",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".html": "HTML",
        ".css": "CSS",
    }
    for ext in sorted(extension_counts):
        language_names.append(extension_map.get(ext, ext))

    return {
        "top_level_dirs": ", ".join(top_level_dirs[:5]) or "(none)",
        "language_summary": ", ".join(language_names[:5]) or "(unknown)",
    }


def _build_prompt(repo_folder_path: str, repo_url: Optional[str] = None) -> str:
    repo_text = _collect_repo_text(repo_folder_path)
    metadata = _compute_repo_metadata(repo_folder_path)

    return "\n".join([
        "You are a senior developer writing documentation for other developers.",
        "Analyse the repository files below and answer each of the following sections:",
        "",
        "1. **Purpose** - What problem does this repo solve in one or two sentences?",
        "2. **How it works** - Key components, architecture, or main flow.",
        "3. **Inputs / Outputs** - What does it take in and produce?",
        "4. **Key dependencies** - Notable libraries or frameworks used.",
        "5. **How to use it** - How would a developer run or integrate this?",
        "",
        f"Repository path: {repo_folder_path}",
        f"Repository URL: {repo_url or 'not provided'}",
        f"Top-level folders: {metadata['top_level_dirs']}",
        f"Main file types: {metadata['language_summary']}",
        "",
        "Repository files:",
        "---",
        repo_text,
        "---",
        "",
        "Write the structured overview now. Be specific — reference actual file names, "
        "function names, and classes where relevant.",
    ])


def _heuristic_repo_summary(repo_folder_path: str, repo_url: Optional[str] = None) -> str:
    metadata = _compute_repo_metadata(repo_folder_path)
    readme_text = ""
    repo_folder = Path(repo_folder_path)

    for readme_name in README_CANDIDATES:
        readme_path = repo_folder / readme_name
        if readme_path.exists():
            readme_text = _read_file_snippet(readme_path, max_chars=1200)
            break

    lines = [line.strip() for line in readme_text.splitlines() if line.strip()]
    readme_summary = lines[0] if lines else "No README summary available."

    # Detect any dependency file present for the heuristic summary
    detected_dep_file = None
    for dep_file in DEPENDENCY_FILES:
        if (repo_folder / dep_file).exists():
            detected_dep_file = dep_file
            break

    # Detect any entry points present for the heuristic summary
    detected_entry_points: List[str] = []
    for root, dirs, files in os.walk(repo_folder_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for file_name in files:
            if file_name.lower() in ENTRY_POINT_NAMES:
                rel = Path(root) / file_name
                detected_entry_points.append(str(Path(rel).relative_to(repo_folder)))
        if len(detected_entry_points) >= 3:
            break

    entry_point_line = ", ".join(detected_entry_points) if detected_entry_points else "none detected"

    return (
        f"Repository overview:\n"
        f"- Repository path: {repo_folder_path}\n"
        f"- GitHub URL: {repo_url or 'not provided'}\n"
        f"- Top-level folders: {metadata['top_level_dirs']}\n"
        f"- Main file types: {metadata['language_summary']}\n"
        f"- Dependency manifest: {detected_dep_file or 'none detected'}\n"
        f"- Entry points: {entry_point_line}\n"
        f"- README summary: {readme_summary}\n\n"
        f"This repository appears to be a project focused on {metadata['language_summary'].lower()} development. "
        f"The README text suggests its purpose is: {readme_summary}"
    )


def generate_repo_overview(repo_folder_path: str, repo_url: Optional[str] = None) -> str:
    if not os.path.isdir(repo_folder_path):
        return "Repository folder not found. Please make sure the repository has been downloaded."

    prompt = _build_prompt(repo_folder_path, repo_url)
    if llama_available():
        result = generate_with_llama(prompt, max_tokens=config.OVERVIEW_MAX_TOKENS)
        if result:
            return result

    return _heuristic_repo_summary(repo_folder_path, repo_url)


def generate_file_overview(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return "File not found."

    content = _read_file_snippet(path, max_chars=10000)
    if not content:
        return "Unable to read file contents."

    if llama_available():
        prompt = "\n".join([
            "You are a senior developer writing documentation for other developers.",
            "Analyse the source file below and answer each of the following sections:",
            "",
            "1. **Purpose** - What is this file's role in one or two sentences? Take note of the file extension for clues. ",
            "2. **Key functions / classes** - What are the main callables and what do they do?",
            "3. **Inputs / Outputs** - What does it accept and return?",
            "4. **Dependencies** - What does it import or rely on?",
            "5. **Usage notes** - Anything a developer should know before using or modifying this file?",
            "",
            f"File name: {path.name}",
            "",
            "File contents:",
            "---",
            content,
            "---",
            "",
            "Write the structured overview now. Be specific — reference actual function names, "
            "classes, and variable names where relevant.",
        ])
        result = generate_with_llama(prompt, max_tokens=config.OVERVIEW_MAX_TOKENS)
        if result:
            return result
        else:
            print("AI GENERATION FAILED") # Debugging output to indicate generation failure
    else:
        print("LLAMA.CPP NOT AVAILABLE - FALLING BACK TO HEURISTIC OVERVIEW")

    first_lines = [line.strip() for line in content.splitlines() if line.strip()]
    if first_lines:
        summary_line = first_lines[0]
    else:
        summary_line = "No meaningful lines could be extracted from the file."

    return (
        f"File overview for {path.name}:\n"
        f"- First meaningful line: {summary_line}\n"
        f"- Size: {path.stat().st_size} bytes\n"
        "This file appears to contain source or documentation content that should be reviewed manually for exact behavior."
    )