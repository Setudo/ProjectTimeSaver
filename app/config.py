# Bridge between python scripts and config toml file

import toml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.toml"

DEFAULT_CONFIG = {
    "ai": {
        "max_tokens": 4096,
        "temperature": 0.4,
        "overview_max_tokens": 4096,
        "explain_max_tokens": 4096,
        "test_max_tokens": 4096,
    },
    "repo": {
        "max_download_size_mb": 200
    }
}


def normalize_keys(config):
    if not isinstance(config, dict):
        return config
    normalized = {}
    for key, value in config.items():
        normalized[key.lower()] = normalize_keys(value) if isinstance(value, dict) else value
    return normalized


def load_config():
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG.copy()

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        user_config = toml.load(f)

    user_config = normalize_keys(user_config)
    return merge_dicts(DEFAULT_CONFIG, user_config)


def save_config(config):
    normalized = normalize_keys(config)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        toml.dump(normalized, f)

    global _config, MAX_TOKENS, TEMPERATURE, MAX_REPO_SIZE_BYTES
    global OVERVIEW_MAX_TOKENS, EXPLAIN_MAX_TOKENS, TEST_MAX_TOKENS
    _config = normalized
    MAX_TOKENS = _config["ai"]["max_tokens"]
    TEMPERATURE = _config["ai"]["temperature"]
    OVERVIEW_MAX_TOKENS = _config["ai"]["overview_max_tokens"]
    EXPLAIN_MAX_TOKENS = _config["ai"]["explain_max_tokens"]
    TEST_MAX_TOKENS = _config["ai"]["test_max_tokens"]
    MAX_REPO_SIZE_BYTES = _config["repo"]["max_download_size_mb"] * 1024 * 1024


def merge_dicts(default, override):
    result = default.copy()
    for key, value in override.items():
        if isinstance(value, dict) and key in result:
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


# Load once
_config = load_config()

# Expose clean variables
MAX_TOKENS = _config["ai"]["max_tokens"]
TEMPERATURE = _config["ai"]["temperature"]
OVERVIEW_MAX_TOKENS = _config["ai"]["overview_max_tokens"]
EXPLAIN_MAX_TOKENS = _config["ai"]["explain_max_tokens"]
TEST_MAX_TOKENS = _config["ai"]["test_max_tokens"]

MAX_REPO_SIZE_BYTES = (
    _config["repo"]["max_download_size_mb"] * 1024 * 1024
)
