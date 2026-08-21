import os
import shutil
from pathlib import Path


def save_file(path: str, content: str) -> None:
    """Save text content to a file."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        

def delete_file(path: str) -> None:
    """Delete a file if it exists."""
    if os.path.exists(path):
        os.remove(path)

def copy_file(src: str, dest: str) -> None:
    """Copy a file to a new location."""
    shutil.copy(src, dest)

def move_file(src: str, dest: str) -> None:
    """Move a file to a new location."""
    shutil.move(src, dest)

def ensure_dir(path: str) -> None:
    """Create a directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)
