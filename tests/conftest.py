import os

# Tests use a throwaway SQLite DB so CI needs no MySQL server.
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/insightiq_ci_test.db")
os.environ.pop("GROQ_API_KEY", None)  # AI calls fall back gracefully in tests
