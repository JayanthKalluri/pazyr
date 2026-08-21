import os
import shutil
from pathlib import Path


class _FilesystemConnection:

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


class FilesystemClient:
    _client: _FilesystemConnection | None = None
    
    @classmethod
    def init(cls) -> _FilesystemConnection:
        client = _FilesystemConnection()
        cls._client = client
        
        return client
    
    @classmethod
    def get(cls) -> _FilesystemConnection:
        if not cls._client:
            raise RuntimeError("FileSystem connection is not established.")
        
        return cls._client
    
    @classmethod
    def shutdown(cls):
        cls._client = None