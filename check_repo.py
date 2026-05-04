#!/usr/bin/env python3
"""Helper script to check a repo and list branches."""

import sys
import os
from git import Repo
from rich.console import Console
from rich.table import Table

console = Console()


def check_repo(repo_path: str):
    """Check repo and list available branches."""

    if not os.path.exists(repo_path):
        console.print(f"[red]✗ Path does not exist: {repo_path}[/red]")
        return

    git_path = os.path.join(repo_path, '.git')
    if not os.path.exists(git_path):
        console.print(f"[red]✗ Not a git repository: {repo_path}[/red]")
        return

    try:
        repo = Repo(repo_path)

        console.print(f"\n[bold cyan]Repository:[/bold cyan] {repo_path}")
        console.print(f"[bold cyan]Current branch:[/bold cyan] {repo.active_branch.name}\n")

        # List all branches
        table = Table(title="Available Branches")
        table.add_column("Branch", style="cyan")
        table.add_column("Last Commit", style="dim")

        current_branch = repo.active_branch.name

        for branch in repo.branches:
            last_commit = branch.commit.message.split('\n')[0][:50]
            branch_name = f"→ {branch.name}" if branch.name == current_branch else f"  {branch.name}"
            table.add_row(branch_name, last_commit)

        console.print(table)

        # Check for TypeScript files
        console.print("\n[bold]Checking for TypeScript/JavaScript files...[/bold]")
        ts_files = []
        for root, dirs, files in os.walk(repo_path):
            # Skip node_modules, .git, dist, build
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist', 'build', '.next']]
            for file in files:
                if file.endswith(('.ts', '.tsx', '.js', '.jsx')):
                    ts_files.append(os.path.relpath(os.path.join(root, file), repo_path))
                    if len(ts_files) >= 10:  # Show first 10
                        break
            if len(ts_files) >= 10:
                break

        if ts_files:
            console.print(f"[green]✓ Found TypeScript/JavaScript files ({len(ts_files)} shown):[/green]")
            for f in ts_files[:10]:
                console.print(f"  - {f}")
        else:
            console.print("[yellow]⚠ No TypeScript/JavaScript files found[/yellow]")

        console.print("\n[bold green]Repository is valid for MR review![/bold green]\n")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("Usage: python check_repo.py /path/to/repo")
        sys.exit(1)

    check_repo(sys.argv[1])
