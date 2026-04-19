import importlib
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

try:
    llama_cpp = importlib.import_module("llama_cpp")
    Llama = llama_cpp.Llama
    _LLAMA_CPP_AVAILABLE = True
except Exception:
    Llama = None
    _LLAMA_CPP_AVAILABLE = False

MODEL_PATH_ENV = "LLAMA_CPP_MODEL_PATH"
README_CANDIDATES = ["README.md", "README.rst", "README.txt", "README"]
COMMON_TEXT_EXTENSIONS = {".md", ".rst", ".txt", ".py", ".js", ".json", ".yaml", ".yml", ".ini", ".cfg", ".toml"}


def _find_local_model_path() -> Optional[str]:
    env_path = os.environ.get(MODEL_PATH_ENV)
    if env_path:
        env_path = os.path.expanduser(env_path)
        if os.path.exists(env_path):
            return env_path

    top_paths = [Path(__file__).resolve().parent, Path.cwd()]
    for base in top_paths:
        for pattern in ["*.gguf", "*.bin", "*.pt", "*.pth"]:
            matches = list(base.glob(pattern))
            if matches:
                return str(matches[0])

    return None


def _read_file_snippet(path: Path, max_chars: int = 14000) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            text = f.read(max_chars)
            return text.strip()
    except Exception:
        return ""


def _collect_repo_text(repo_folder_path: str) -> str:
    repo_folder = Path(repo_folder_path)
    snippets: List[str] = []

    for readme_name in README_CANDIDATES:
        readme_path = repo_folder / readme_name
        if readme_path.exists():
            content = _read_file_snippet(readme_path, max_chars=12000)
            if content:
                snippets.append(f"README ({readme_name}):\n{content}")
                break

    top_files = []
    for entry in sorted(repo_folder.iterdir()):
        if entry.is_file() and entry.suffix.lower() in COMMON_TEXT_EXTENSIONS:
            top_files.append(entry)
        if len(top_files) >= 4:
            break

    if top_files:
        for file_path in top_files[:3]:
            snippet = _read_file_snippet(file_path, max_chars=3000)
            if snippet:
                snippets.append(f"File: {file_path.name}\n{snippet}")

    if not snippets:
        snippets.append("No README or common text files could be read from the repository.")

    return "\n\n".join(snippets)


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
    prompt_parts = [
        "You are a helpful assistant that summarizes code repositories.",
        "Read the repository description and top file contents below, then provide a short overview of the purpose of the repo.",
        f"Repository path: {repo_folder_path}",
    ]
    if repo_url:
        prompt_parts.append(f"Repository URL: {repo_url}")

    prompt_parts.extend([
        f"Top-level folders: {metadata['top_level_dirs']}",
        f"Main file types: {metadata['language_summary']}",
        "Repository source content:\n",
        repo_text,
    ])
    prompt_parts.append("\nWrite a concise summary of what this repository is for and how a developer might use it.")
    return "\n".join(prompt_parts)


def _llama_available() -> bool:
    if not _LLAMA_CPP_AVAILABLE:
        return False
    model_path = _find_local_model_path()
    return bool(model_path)


def _generate_with_llama(prompt: str) -> Optional[str]:
    model_path = _find_local_model_path()
    if not model_path or not _LLAMA_CPP_AVAILABLE:
        return None

    try:
        llama = Llama(model_path=model_path)
        response = llama.create(prompt=prompt, max_tokens=256, temperature=0.2)
        text = response.get("choices", [{}])[0].get("text")
        return text.strip() if isinstance(text, str) else None
    except Exception:
        return None


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

    return (
        f"Repository overview:\n"
        f"- Repository path: {repo_folder_path}\n"
        f"- GitHub URL: {repo_url or 'not provided'}\n"
        f"- Top-level folders: {metadata['top_level_dirs']}\n"
        f"- Main file types: {metadata['language_summary']}\n"
        f"- README summary: {readme_summary}\n\n"
        f"This repository appears to be a project focused on {metadata['language_summary'].lower()} development. "
        f"The README text suggests its purpose is: {readme_summary}"
    )


def generate_repo_overview(repo_folder_path: str, repo_url: Optional[str] = None) -> str:
    if not os.path.isdir(repo_folder_path):
        return "Repository folder not found. Please make sure the repository has been downloaded."

    prompt = _build_prompt(repo_folder_path, repo_url)
    if _llama_available():
        result = _generate_with_llama(prompt)
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

    if _llama_available():
        prompt = (
            "You are a helpful assistant summarizing a source file.\n"
            f"File name: {path.name}\n"
            f"File contents:\n{content}\n\n"
            "Provide a concise overview of this file's purpose and main responsibilities."
        )
        result = _generate_with_llama(prompt)
        if result:
            return result

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

