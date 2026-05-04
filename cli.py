#!/usr/bin/env python3
"""CLI for MR Review Agent."""

import os
import sys
from pathlib import Path
from datetime import datetime
import typer
from rich.console import Console
from rich.markdown import Markdown

from core.orchestrator import ReviewOrchestrator

app = typer.Typer(help="Local AI-powered MR Review Agent")
console = Console()


@app.command()
def review(
    base_branch: str = typer.Option("main", "--base", "-b", help="Base branch to compare against"),
    model: str = typer.Option("gemma4:26b", "--model", "-m", help="Ollama model to use"),
    output: str = typer.Option("./REVIEW.md", "--output", "-o", help="Output file path"),
    repo_path: str = typer.Option(".", "--repo", "-r", help="Repository path")
):
    """
    Run MR review on current branch.

    This will:
    1. Parse git diff against base branch
    2. Extract functions and interfaces using AST
    3. Detect signature changes (BLOCKER priority)
    4. Build call graph for changed functions
    5. Find duplicate code/interfaces
    6. Generate review using local LLM (Ollama)
    """
    repo_path = os.path.abspath(repo_path)

    # Validate repo
    if not os.path.exists(os.path.join(repo_path, '.git')):
        console.print("[red]Error: Not a git repository[/red]")
        sys.exit(1)

    try:
        # Execute review
        orchestrator = ReviewOrchestrator(repo_path, base_branch, model)
        review_markdown = orchestrator.execute_review()

        # Write to file
        output_path = Path(output)
        output_path.write_text(review_markdown, encoding='utf-8')

        console.print(f"\n[bold green]✓ Review saved to {output}[/bold green]\n")

        # Display preview
        console.print("[bold]Review Preview:[/bold]")
        console.print(Markdown(review_markdown[:1000] + "\n\n...(truncated)"))

    except KeyboardInterrupt:
        console.print("\n[yellow]Review cancelled[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@app.command()
def init():
    """Initialize .reviewrc configuration file."""
    config = """{
  "model": {
    "name": "gemma2:27b",
    "temperature": 0.2
  },
  "review": {
    "base_branch": "main",
    "output_path": "./REVIEW.md"
  },
  "duplicate_detection": {
    "similarity_threshold": 0.85
  }
}"""

    config_path = Path(".reviewrc")
    if config_path.exists():
        console.print("[yellow].reviewrc already exists[/yellow]")
        return

    config_path.write_text(config)
    console.print("[green]✓ Created .reviewrc[/green]")


@app.command()
def version():
    """Show version information."""
    console.print("[bold cyan]MR Review Agent v0.1.0[/bold cyan]")
    console.print("Local AI-powered code review using Ollama")


@app.command()
def test_ollama(model: str = typer.Option("gemma4:26b", "--model", "-m")):
    """Test if Ollama is working with the specified model."""
    import ollama

    console.print(f"Testing connection to Ollama with model: {model}")

    try:
        response = ollama.generate(
            model=model,
            prompt="Say 'OK' if you can read this.",
            options={'num_predict': 10}
        )

        console.print(f"[green]✓ Ollama is working![/green]")
        console.print(f"Response: {response['response']}")

    except Exception as e:
        console.print(f"[red]✗ Ollama test failed: {e}[/red]")
        console.print("\nMake sure:")
        console.print("1. Ollama is running (run 'ollama serve')")
        console.print(f"2. Model '{model}' is pulled (run 'ollama pull {model}')")
        sys.exit(1)


if __name__ == "__main__":
    app()
