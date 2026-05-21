"""
Central settings for Dakota Joe prompt automation.

Override login values with environment variables (see `.env`):
  DAKOTA_BASE_URL, DAKOTA_USERNAME, DAKOTA_PASSWORD
"""

import os

# Project root (folder that contains this file).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv():
    """Load KEY=VALUE lines from `.env` when present (does not override existing env vars)."""
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ and value:
                os.environ[key] = value


_load_dotenv()


def _env_or_default(name, default):
    """Use the default when the environment variable is missing or blank."""
    value = os.getenv(name)
    if value is None or not str(value).strip():
        return default
    return str(value).strip()


def project_path(*parts):
    """Build an absolute path under the automation project folder."""
    return os.path.join(BASE_DIR, *parts)


# --- Prompt source (read-only during runs) ---
PROMPTS_FILE = "Prompts.csv"

# --- Markets (environment / site profiles) ---
DEFAULT_MARKET = "marketplace"

# Keys: marketplace | sandbox | uat | custom
# Override URLs via Jenkins/env: DAKOTA_SANDBOX_URL, DAKOTA_UAT_URL, DAKOTA_BASE_URL (custom)
MARKET_PROFILES = {
    "marketplace": {
        "label": "Production Marketplace",
        "base_url": "https://dakotanetworks.my.site.com/dakotaMarketplace/s/",
        "prompts_file": "Prompts.csv",
    },
    "sandbox": {
        "label": "Sandbox",
        "base_url_env": "DAKOTA_SANDBOX_URL",
        "prompts_file": "Prompts.sandbox.csv",
    },
    "uat": {
        "label": "UAT",
        "base_url_env": "DAKOTA_UAT_URL",
        "prompts_file": "Prompts.uat.csv",
    },
    "custom": {
        "label": "Custom",
        "base_url_env": "DAKOTA_BASE_URL",
        "prompts_file": "Prompts.csv",
    },
}


def _normalize_base_url(url):
    """Ensure marketplace URLs end with / for Salesforce community paths."""
    url = (url or "").strip()
    if not url:
        return ""
    if url.endswith("/") or "?" in url:
        return url
    return url + "/"


def resolve_market_profile(market_key=None, base_url_override=None):
    """Resolve market key to base URL, prompts file, and labels.

    Raises ValueError when the market is unknown or its URL is not configured.
    """
    key = (market_key or os.getenv("DAKOTA_MARKET") or DEFAULT_MARKET).strip().lower()
    if key not in MARKET_PROFILES:
        known = ", ".join(sorted(MARKET_PROFILES.keys()))
        raise ValueError(f"Unknown market '{market_key}'. Choose one of: {known}")

    spec = MARKET_PROFILES[key]
    profile = {
        "key": key,
        "label": spec.get("label", key),
        "prompts_file": spec.get("prompts_file") or PROMPTS_FILE,
    }

    if base_url_override and str(base_url_override).strip():
        url = str(base_url_override).strip()
    elif spec.get("base_url"):
        url = spec["base_url"]
    elif spec.get("base_url_env"):
        url = _env_or_default(spec["base_url_env"], "")
    else:
        url = ""

    url = _normalize_base_url(url)
    if not url:
        env_hint = spec.get("base_url_env") or "DAKOTA_BASE_URL"
        raise ValueError(
            f"Market '{key}' has no base URL configured. "
            f"Set {env_hint} in Jenkins job parameters, agent environment, or .env."
        )

    profile["base_url"] = url
    prompts_path = project_path(profile["prompts_file"])
    if not os.path.exists(prompts_path) and profile["prompts_file"] != PROMPTS_FILE:
        profile["prompts_file"] = PROMPTS_FILE
        prompts_path = project_path(PROMPTS_FILE)
    profile["prompts_path"] = prompts_path
    return profile


def market_choices():
    """Sorted market keys for CLI/Jenkins choice lists."""
    return sorted(MARKET_PROFILES.keys())


# --- Marketplace login (default market until apply_market / CLI runs) ---
_active = resolve_market_profile(DEFAULT_MARKET)
URL = _active["base_url"]
USERNAME = _env_or_default("DAKOTA_USERNAME", "aleeta.fatima@dakota.net.marketplace")
PASSWORD = _env_or_default("DAKOTA_PASSWORD", "Agent2026")

OBJECT_TYPE_COL = "hi"
PROMPT_COL = "Prompt"
MARKER_COL = "Marker"
SMOKE_MARKER = "smoke"
# Accepted header labels for the prompt column in older CSV exports.
PROMPT_HEADER_NAMES = ("Prompt", "Prompt Text")

# Each object row in Prompts.csv is executed this many times.
RUNS_PER_OBJECT = 3

# --- Timing (seconds) ---
RESPONSE_TIMEOUT = 100
CONSOLE_EVENT_WAIT_SECONDS = 2
PAGE_IDLE_AFTER_LOGIN = 10
CHAT_RECOVERY_SLEEP_SECONDS = 10

# --- Chat UI coordinates (bottom-right input, from window edges) ---
CHAT_INPUT_X_OFFSET = -250
CHAT_INPUT_Y_OFFSET = -70

# --- Chat interaction strategy ---
# Prefer element-based interactions for CI stability.
USE_DOM_FIRST_CHAT_OPEN = True
USE_DOM_FIRST_SEND = True
# Keep coordinate fallback enabled to preserve current behavior if DOM lookup fails.
ENABLE_COORDINATE_FALLBACK = True

# --- Output locations (relative to BASE_DIR) ---
SCREENSHOTS_DIR = "screenshots"
PERFORMANCE_RESULTS_XLSX = "Performance evaluation results.xlsx"
ALLURE_RESULTS_DIR = "allure-results"
ALLURE_REPORT_DIR = "allure-report"

# Optional legacy columns on a CSV source file; results are written back only when all three exist.
AUTOMATION_STATUS_COL = "Automation Status"
AUTOMATION_LINK_COL = "Automation Link"
AUTOMATION_TIME_COL = "Automation Time (s)"
