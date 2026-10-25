import os
import time
import hashlib

def cache_path(cache_dir: str, key: str) -> str:
    os.makedirs(cache_dir, exist_ok=True)
    digest = hashlib.md5(key.encode()).hexdigest()[:12]
    return os.path.join(cache_dir, f"{digest}.html")

def is_cache_fresh(filepath: str, ttl_seconds: int) -> bool:
    if not os.path.exists(filepath):
        return False
    age = time.time() - os.path.getmtime(filepath)
    return age < ttl_seconds

def save_cache(filepath: str, html: str):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

def load_cache(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()
