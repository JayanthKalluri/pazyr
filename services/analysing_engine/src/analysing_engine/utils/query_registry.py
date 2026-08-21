from pathlib import Path

class QueryRegistry:
    def __init__(self, sql_dir: Path = None):
        self._sql_dir = sql_dir
        self._queries: dict[str, str] = {}

        print(self._sql_dir)
        for file in self._sql_dir.rglob("*.sql"):
            key = ".".join(file.relative_to(self._sql_dir).with_suffix("").parts)
            print(key)

            self._queries[key] = file.read_text(encoding="utf-8")

    def get(self, name: str) -> str:
        try:
            return self._queries[name]
        except KeyError:
            raise ValueError(f"SQL query '{name}' not found") from None
