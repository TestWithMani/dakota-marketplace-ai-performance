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


# --- Marketplace login ---
URL = _env_or_default(
    "DAKOTA_BASE_URL",
    "https://dakotanetworks.my.site.com/dakotaMarketplace/s/",
)
USERNAME = _env_or_default("DAKOTA_USERNAME", "aleeta.fatima@dakota.net.marketplace")
PASSWORD = _env_or_default("DAKOTA_PASSWORD", "Agent2026")

# --- Prompt source (read-only during runs) ---
PROMPTS_FILE = "Prompts.csv"
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
