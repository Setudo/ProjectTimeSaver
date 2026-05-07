import importlib
import os
from pathlib import Path
from typing import Optional, List

import config

MODEL_PATH_ENV = "LLAMA_CPP_MODEL_PATH"
MODELS_DIR = Path(__file__).parent / "models"

# System message used for all AI generation tasks
_SYSTEM_MESSAGE = (
    "You are a senior software developer assistant. "
    "Provide clear, accurate, and concise responses."
)

# Per-model context budgets: (n_ctx, max_prompt_chars)
# max_prompt_chars is the character limit for the raw prompt content fed to the model.
# Keeping prompt well under n_ctx leaves enough room for a useful response.
_MODEL_PROFILES = {
    "tinyllama": {"n_ctx": 2048, "max_prompt_chars": 1800},
}
_DEFAULT_PROFILE = {"n_ctx": 4096, "max_prompt_chars": 6000}

try:
    llama_cpp = importlib.import_module("llama_cpp")
    Llama = llama_cpp.Llama
    _LLAMA_CPP_AVAILABLE = True
except Exception:
    print("\nNO AI AVAILABLE\n")
    Llama = None
    _LLAMA_CPP_AVAILABLE = False

# Cache for Llama instances to avoid multiple loads
_llama_cache = {}


def get_available_models() -> List[str]:
    """Return a sorted list of .gguf model filenames found in the models directory."""
    if not MODELS_DIR.exists():
        return []
    return sorted(p.name for p in MODELS_DIR.glob("*.gguf"))


def _get_model_profile(model_name: str) -> dict:
    """Return the context profile dict for a given model filename."""
    name_lower = model_name.lower()
    for key, profile in _MODEL_PROFILES.items():
        if key in name_lower:
            return profile
    return _DEFAULT_PROFILE


def get_model_context_budget(model_name: Optional[str] = None) -> int:
    """
    Return the maximum number of characters that should be used for prompt
    content for the currently selected (or given) model.

    Callers use this to cap how much repo text they include in a prompt so
    the model always has room to produce a coherent response.
    """
    if not model_name:
        path = find_local_model_path()
        model_name = Path(path).name if path else ""
    return _get_model_profile(model_name)["max_prompt_chars"]


def _get_prompt_format(model_name: str) -> str:
    """
    Detect the prompt format required by a model based on its filename.

    Returns one of:
      "tinyllama"  - TinyLlama chat format  (<|system|> / <|user|> / <|assistant|>)
      "plain"      - Raw prompt passed through unchanged (default for Llama 3.x etc.)
    """
    name_lower = model_name.lower()
    if "tinyllama" in name_lower:
        return "tinyllama"
    return "plain"


def _get_stop_sequences(model_name: str) -> List[str]:
    """Return appropriate stop sequences for the model."""
    fmt = _get_prompt_format(model_name)
    if fmt == "tinyllama":
        return ["</s>", "<|user|>", "<|system|>"]
    return []


def _format_prompt(raw_prompt: str, model_name: str) -> str:
    """
    Wrap *raw_prompt* in the chat template required by *model_name*.

    TinyLlama template:
        <|system|>
        {system_message}</s>
        <|user|>
        {prompt}</s>
        <|assistant|>

    All other models receive the prompt unchanged.
    """
    fmt = _get_prompt_format(model_name)
    if fmt == "tinyllama":
        return (
            f"<|system|>\n{_SYSTEM_MESSAGE}</s>\n"
            f"<|user|>\n{raw_prompt}</s>\n"
            f"<|assistant|>\n"
        )
    # Plain / Llama 3.x — pass through as-is
    return raw_prompt


def find_local_model_path(model_name: Optional[str] = None) -> Optional[str]:
    """
    Resolve the full path to the model to use.

    Priority order:
      1. *model_name* argument (filename only, looked up in MODELS_DIR)
      2. config.SELECTED_MODEL (saved setting)
      3. LLAMA_CPP_MODEL_PATH environment variable
      4. First .gguf file found in the standard search directories
    """
    # 1. Explicit argument
    if model_name:
        candidate = MODELS_DIR / model_name
        if candidate.exists():
            return str(candidate)
        print(f"Requested model '{model_name}' not found in {MODELS_DIR}")

    # 2. Config setting
    selected = getattr(config, "SELECTED_MODEL", "")
    if selected:
        candidate = MODELS_DIR / selected
        if candidate.exists():
            print(f"Using configured model: {candidate}")
            return str(candidate)
        print(f"Configured model '{selected}' not found in {MODELS_DIR}, falling back.")

    # 3. Environment variable
    env_path = os.environ.get(MODEL_PATH_ENV)
    print("ENV PATH:", env_path)
    if env_path:
        env_path = os.path.expanduser(env_path)
        if os.path.exists(env_path):
            return env_path
        print(f"Environment variable {MODEL_PATH_ENV} points to '{env_path}', but the file does not exist.")

    # 4. Auto-discover first available model
    search_dirs = [
        MODELS_DIR,
        Path(__file__).parent,
        Path.cwd(),
        Path.home() / "models",
        Path.home() / ".models",
    ]
    for base in search_dirs:
        if not base.exists():
            continue
        for pattern in ["*.gguf", "*.bin"]:
            matches = sorted(base.glob(pattern))
            if matches:
                print(f"Auto-discovered model: {matches[0]}")
                return str(matches[0])

    return None


def llama_available() -> bool:
    if not _LLAMA_CPP_AVAILABLE:
        return False
    return bool(find_local_model_path())


def generate_with_llama(raw_prompt: str, max_tokens: Optional[int] = None) -> Optional[str]:
    """
    Generate a completion for *raw_prompt* using the currently configured model.

    The prompt is automatically wrapped in the correct chat template for the
    selected model before being sent to llama.cpp.  Repetition penalties and
    stop sequences are applied automatically based on the model type.
    """
    model_path = find_local_model_path()
    print("PATH:", model_path)
    if not model_path or not _LLAMA_CPP_AVAILABLE:
        return None

    model_name = Path(model_path).name
    profile = _get_model_profile(model_name)
    prompt = _format_prompt(raw_prompt, model_name)
    stop_sequences = _get_stop_sequences(model_name)
    repeat_penalty = getattr(config, "REPEAT_PENALTY", 1.15)

    print(f"Generating with model: {model_name}  |  max_tokens: {max_tokens}  |  repeat_penalty: {repeat_penalty}")

    effective_max_tokens = max_tokens if max_tokens is not None else config.MAX_TOKENS

    # Check cache
    cache_key = model_path
    if cache_key not in _llama_cache:
        try:
            _llama_cache[cache_key] = Llama(
                model_path=model_path,
                n_ctx=profile["n_ctx"],
                verbose=False,
            )
        except Exception as e:
            print(f"Error loading Llama model: {e}")
            return None

    llama = _llama_cache[cache_key]

    try:
        kwargs = dict(
            prompt=prompt,
            max_tokens=effective_max_tokens,
            temperature=config.TEMPERATURE,
            repeat_penalty=repeat_penalty,
        )
        if stop_sequences:
            kwargs["stop"] = stop_sequences

        response = llama.create_completion(**kwargs)
        print("\nResponse:", response, "\n")
        text = response.get("choices", [{}])[0].get("text")
        print("\nGenerated Text:", text, "\n")
        return text.strip() if isinstance(text, str) else None
    except Exception as e:
        print(f"Error during Llama generation: {e}")
        return None


def read_text_safe(path: Path, max_chars: int = 25000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except Exception:
        return ""
