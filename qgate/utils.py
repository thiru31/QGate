import os
from pathlib import Path

def default_key_path():
    # same default as your bat
    home = Path.home()
    return str(home / "Downloads" / "qdc123.pem")

def load_template(name="tunnel.bat"):
    # templates live inside the package
    package_dir = Path(__file__).resolve().parent
    templates_dir = package_dir / "templates"
    path = templates_dir / name
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    return path.read_text(encoding="utf-8")
