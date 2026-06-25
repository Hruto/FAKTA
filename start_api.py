"""
FAKTA API Launcher — Clean SSL Setup.
Run as: python start_api.py
"""

import os
import sys

# ============================================================
# SSL: use certifi's CA bundle. No Windows store manipulation.
# ============================================================
try:
    import certifi
    ca = certifi.where()
    os.environ["SSL_CERT_FILE"] = ca
    os.environ["REQUESTS_CA_BUNDLE"] = ca
    print(f"[SSL] Using certifi CA bundle: {ca}")
except ImportError:
    print("[SSL] certifi not installed — using system defaults")

# Disable noisy telemetry
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "false"

# ============================================================
# Launch API
# ============================================================
sys.path.insert(0, str(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import app
import uvicorn

print("\n[API] Starting FAKTA API server on http://0.0.0.0:8000")
print("[API] Press Ctrl+C to stop\n")

uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
