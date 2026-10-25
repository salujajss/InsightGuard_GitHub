import os
from pathlib import Path

# Try to load dotenv for local development (safe no-op if not installed/missing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to load from Streamlit secrets (Streamlit Cloud deployment)
def _get_secret(key):
    """Read from st.secrets if available, else fall back to env var."""
    try:
        import streamlit as st
        return st.secrets.get(key)
    except Exception:
        return None

def get_config(key):
    """Return config value: st.secrets first, then env var."""
    val = _get_secret(key)
    if val:
        return val
    return os.getenv(key)

BASE_DIR       = Path(__file__).resolve().parent.parent
DATA_FILE      = BASE_DIR / "data" / "business_data.xlsx"
OUTPUT_DIR     = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

EMAIL_SENDER   = get_config("EMAIL_SENDER")
EMAIL_PASSWORD = get_config("EMAIL_PASSWORD")
EMAIL_RECEIVER = get_config("EMAIL_RECEIVER")
THRESHOLD      = 20
