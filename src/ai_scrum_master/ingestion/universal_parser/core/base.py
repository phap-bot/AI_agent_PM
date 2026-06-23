from abc import ABC, abstractmethod
from pathlib import Path

class BaseParser(ABC):
    """Abstract base class for all file parsers."""

    @abstractmethod
    def parse(self, file_path: Path, output_dir: Path) -> str:
        """
        Parse the given file and return its content as a Markdown string.
        Any extracted assets (like images) should be saved within an 'assets' folder
        inside the specified output_dir.
        """
        pass
