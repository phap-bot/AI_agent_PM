from pathlib import Path
from typing import Type

from .base import BaseParser
from .parsers.pdf_handler import PdfParser
from .parsers.docx_handler import DocxParser
from .parsers.txt_handler import TxtParser
from .parsers.md_handler import MdParser

class ParserRouter:
    """Routes files to their appropriate parser based on extension."""

    @staticmethod
    def get_parser(file_path: Path) -> BaseParser:
        ext = file_path.suffix.lower()
        
        if ext == ".pdf":
            return PdfParser()
        if ext == ".docx":
            return DocxParser()
        if ext == ".txt":
            return TxtParser()
        if ext == ".md":
            return MdParser()
            
        raise ValueError(f"Unsupported file format: {ext}")
