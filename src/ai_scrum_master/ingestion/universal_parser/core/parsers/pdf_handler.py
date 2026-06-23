import fitz
from pathlib import Path
from loguru import logger

from ..base import BaseParser

class PdfParser(BaseParser):
    """Parser for PDF files using PyMuPDF (fitz)."""

    def parse(self, file_path: Path, output_dir: Path) -> str:
        logger.info(f"Parsing PDF: {file_path}")
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            logger.error(f"Failed to open PDF {file_path}: {e}")
            raise

        assets_dir = output_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        md_lines: list[str] = []
        image_count = 0

        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text
            text = page.get_text()
            if text:
                md_lines.append(text)
            
            # Extract images
            image_list = page.get_images(full=True)
            for img in image_list:
                xref = img[0]
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    image_filename = f"{file_path.stem}_p{page_num+1}_img{image_count}.{image_ext}"
                    image_path = assets_dir / image_filename
                    
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)
                        
                    md_lines.append(f"\n![Image](assets/{image_filename})\n")
                    image_count += 1
                except Exception as e:
                    logger.warning(f"Failed to extract image {xref} on page {page_num+1}: {e}")

        return "\n".join(md_lines)
