import typer
from pathlib import Path
from loguru import logger

from .core.router import ParserRouter
from .core.post_processor import PostProcessor

app = typer.Typer(help="Universal-to-Markdown Document Parser")

@app.command()
def convert(
    input_path: Path = typer.Argument(..., help="Path to the input file (PDF, DOCX, TXT, MD)"),
    output_dir: Path = typer.Option(None, "--output-dir", "-o", help="Directory to save the markdown file and assets. Defaults to current directory."),
):
    """
    Convert a document to Markdown and extract assets.
    """
    if not input_path.exists():
        logger.error(f"File not found: {input_path}")
        raise typer.Exit(1)
        
    if not input_path.is_file():
        logger.error(f"Path is not a file: {input_path}")
        raise typer.Exit(1)

    if output_dir is None:
        output_dir = Path.cwd()
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting conversion for {input_path.name}")
    
    try:
        parser = ParserRouter.get_parser(input_path)
        raw_markdown = parser.parse(input_path, output_dir)
        
        logger.info("Applying post-processing...")
        cleaned_markdown = PostProcessor.process(raw_markdown)
        
        output_file = output_dir / f"{input_path.stem}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cleaned_markdown)
            
        logger.info(f"Conversion complete! Output saved to: {output_file}")
        
    except ValueError as ve:
        logger.error(ve)
        raise typer.Exit(1)
    except ImportError as ie:
        logger.error(ie)
        raise typer.Exit(1)
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
