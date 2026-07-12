import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def count():
    guests_file = BASE_DIR / "guests_converted.json"
    guests = json.loads(guests_file.read_text())
    return len(guests)

if __name__ == "__main__":
    print(f"Total guest accounts found: {count()}")
