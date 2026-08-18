"""AI Video Subtitle Enhanced Launcher - Pre-flight checks + logging."""
import subprocess, sys, os, shutil, socket
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
LOG_DIR = SCRIPT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"startup_{datetime.now():%Y%m%d_%H%M%S}.log"

def log(msg):
    line = f"[{datetime.now():%H:%M:%S}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def check_package(name, import_name=None):
    import_name = import_name or name
    try:
        mod = __import__(import_name)
        return getattr(mod, "__version__", "ok")
    except ImportError:
        return None

def main():
    errors = []
    warnings = []

    # Python
    log(f"Python: {sys.version.split()[0]} ({sys.executable})")

    # Packages
    for pkg, imp in [("streamlit", None), ("json_repair", "json_repair")]:
        if not check_package(pkg, imp):
            errors.append(f"{pkg} not installed. Run: python install.py")

    # ffmpeg
    if not shutil.which("ffmpeg"):
        errors.append("ffmpeg not found in PATH. Install: choco install ffmpeg")

    # Port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", 8501)) == 0:
            warnings.append("Port 8501 in use. Close other app or use --server.port 8502")

    # Log everything
    for w in warnings:
        log(f"[WARN] {w}")
    for e in errors:
        log(f"[ERROR] {e}")

    # Show problems if any, otherwise stay quiet
    if errors:
        print()
        for e in errors:
            print(f"  [ERROR] {e}")
        print(f"\n  Fix errors above. Log: {LOG_FILE}\n")
        sys.exit(1)
    if warnings:
        print()
        for w in warnings:
            print(f"  [WARN] {w}")
        print()

    # Launch
    log("Launching Streamlit...")
    os.environ["PYTHONWARNINGS"] = "ignore"
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "st.py",
             "--logger.level", "error"],
            cwd=str(SCRIPT_DIR),
        )
        if proc.returncode != 0:
            log(f"Streamlit exited with code {proc.returncode}")
            print(f"\n  Streamlit crashed (code {proc.returncode}). See: {LOG_FILE}\n")
            sys.exit(proc.returncode)
    except KeyboardInterrupt:
        log("Stopped by user")

if __name__ == "__main__":
    main()
