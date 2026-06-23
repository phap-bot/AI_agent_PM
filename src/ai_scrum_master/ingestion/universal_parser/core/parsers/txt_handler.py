from pathlib import Path
from loguru import logger

from ..base import BaseParser

class TxtParser(BaseParser):
    """Parser for simple TXT files."""

    def parse(self, file_path: Path, output_dir: Path) -> str:
        logger.info(f"Parsing TXT: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read TXT {file_path}: {e}")
            raise
