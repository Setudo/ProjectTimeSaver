import importlib
import os
from pathlib import Path
from typing import Optional

import config

MODEL_PATH_ENV = "LLAMA_CPP_MODEL_PATH"

try:
    llama_cpp = importlib.import_module("llama_cpp")
    Llama = llama_cpp.Llama
    _LLAMA_CPP_AVAILABLE = True
except Exception:
    print("\nNO AI AVAILABLE\n")
    Llama = None
    _LLAMA_CPP_AVAILABLE = False


def find_local_model_path() -> Optional[str]:
    env_path = os.environ.get(MODEL_PATH_ENV)
    if env_path:
        env_path = os.path.expanduser(env_path)
        if os.path.exists(env_path):
            return env_path

    search_dirs = [
        Path.cwd(),
        Path(__file__).parent,
        Path(__file__).parent / "models",
        Path.home() / "models",
        Path.home() / ".models",
    ]

    for base in search_dirs:
        if not base.exists():
            continue
        for pattern in ["*.gguf", "*.bin"]:
            matches = list(base.glob(pattern))
            if matches:
                return str(matches[0])

    return None


def llama_available() -> bool:
    if not _LLAMA_CPP_AVAILABLE:
        return False
    return bool(find_local_model_path())


def generate_with_llama(prompt: str, max_tokens: Optional[int] = None) -> Optional[str]:
    model_path = find_local_model_path()
    if not model_path or not _LLAMA_CPP_AVAILABLE:
        return None

    # Use the provided max_tokens, falling back to the global config value
    effective_max_tokens = max_tokens if max_tokens is not None else config.MAX_TOKENS

    try:
        llama = Llama(model_path=model_path, n_ctx=4096, verbose=False)
        response = llama.create_completion(prompt=prompt, max_tokens=effective_max_tokens, temperature=config.TEMPERATURE)
        print("\nResponse:",response,"\n") # Debugging output
        text = response.get("choices", [{}])[0].get("text")
        print("\nGenerated Text:",text,"\n") # Debugging output
        return text.strip() if isinstance(text, str) else None
    except Exception as e:
        print(f"Error during Llama generation: {e}")
        return None


def read_text_safe(path: Path, max_chars: int = 14000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except Exception:
        return ""
