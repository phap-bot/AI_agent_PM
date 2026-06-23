import re

class PostProcessor:
    """Handles post-processing of extracted text to fix common parsing artifacts."""

    @staticmethod
    def process(text: str) -> str:
        """Run all post-processing steps on the text."""
        if not text:
            return ""
        
        text = PostProcessor._clean_broken_lines(text)
        text = PostProcessor._normalize_spacing(text)
        return text.strip() + "\n"

    @staticmethod
    def _clean_broken_lines(text: str) -> str:
        """Join lines that were incorrectly broken across PDF pages or columns."""
        # Join words broken by hyphens at the end of a line
        text = re.sub(r'(\w+)-\n\s*(\w+)', r'\1\2', text)
        
        # Join lines where the first line doesn't end with punctuation 
        # and the second line starts with a lowercase letter.
        # Excludes lines that look like list items or headings.
        lines = text.split("\n")
        cleaned_lines: list[str] = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                cleaned_lines.append(line)
                continue
                
            if cleaned_lines and cleaned_lines[-1].strip():
                prev_line = cleaned_lines[-1].strip()
                # Check if previous line lacks ending punctuation
                if not re.search(r'[.!?:]$', prev_line):
                    # Check if current line starts with lowercase letter (not a heading, list, etc)
                    if re.match(r'^[a-z]', stripped):
                        # Join them
                        cleaned_lines[-1] = cleaned_lines[-1].rstrip() + " " + stripped
                        continue
                        
            cleaned_lines.append(line)
            
        return "\n".join(cleaned_lines)

    @staticmethod
    def _normalize_spacing(text: str) -> str:
        """Remove excessive newlines and spaces."""
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text
