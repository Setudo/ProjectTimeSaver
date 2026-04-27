# Bridge between python scripts and config toml file

import toml
from pathlib import Path

CONFIG_PATH = Path("config.toml")

DEFAULT_CONFIG = {
    "ai": {
        "max_tokens": 1024,
        "temperature": 0.4
    },
    "repo": {
        "max_download_size_mb": 200
    }
}

def load_config():
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG

    with open(CONFIG_PATH, "rb") as f:
        user_config = toml.load(f)

    return merge_dicts(DEFAULT_CONFIG, user_config)


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

MAX_REPO_SIZE_BYTES = (
    _config["repo"]["max_download_size_mb"] * 1024 * 1024
)