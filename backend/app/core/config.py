import os
from pathlib import Path

# Resolve paths relative to app structure
repo_root = Path(__file__).resolve().parents[3]
if repo_root == Path("/") and Path("/app").exists():
    repo_root = Path("/app")

uploads_dir = repo_root / "backend" / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)

# Save the SQLite database file inside the uploads directory to leverage the persistent volume mount
DB_PATH = uploads_dir / "poultry.db"

# Check database connection details
DATABASE_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = DATABASE_URL is not None
