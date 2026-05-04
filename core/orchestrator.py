"""Main orchestrator - coordinates all skills."""

import os
import traceback
from typing import List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from core.models import ContextPacket, FileDiff, FunctionNode, InterfaceNode, CallGraph
from skills.git_parser import parse_git_diff
from skills.ast_parser import parse_typescript_file
from skills.signature_tracker import detect_signature_changes
from skills.graph_builder import build_call_graph
from skills.duplicate_detector import find_duplicates
from skills.context_packager import package_context
from skills.review_generator import generate_review
from skills.diff_analyzer import get_changed_function_names


console = Console()


def log_step(step_name: str, details: str = ""):
    """Log a step with timestamp."""
    import time
    timestamp = time.strftime("%H:%M:%S")
    console.print(f"[dim]{timestamp}[/dim] [cyan]{step_name}[/cyan] {details}")


class ReviewOrchestrator:
    """Orchestrate the MR review process."""

    def __init__(self, repo_path: str, base_branch: str = "main", model: str = "gemma4:26b"):
        self.repo_path = repo_path
        self.base_branch = base_branch
        self.model = model

    def execute_review(self) -> str:
        """
        Execute the full MR review process.

        Returns the review markdown.
        """
        console.print(Panel.fit(
            "[bold cyan]MR Review Agent[/bold cyan]\n"
            f"Repository: {self.repo_path}\n"
            f"Base branch: {self.base_branch}\n"
            f"Model: {self.model}",
            border_style="cyan"
        ))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            # Phase 1: Parse git diff
            task1 = progress.add_task("[cyan]Parsing git diff...", total=None)
            log_step("Phase 1", f"Parsing git diff against {self.base_branch}")
            try:
                branch_name, changed_files = parse_git_diff(self.repo_path, self.base_branch)
                progress.update(task1, completed=True)
                console.print(f"✓ Found {len(changed_files)} changed files")
                for f in changed_files:
                    log_step("  -", f"{f.path} ({f.change_type})")
            except Exception as e:
                progress.update(task1, completed=True)
                console.print(f"[red]✗ Git parsing failed: {e}[/red]")
                traceback.print_exc()
                raise

            if not changed_files:
                return "No TypeScript/JavaScript files changed."

            # Phase 2: Parse changed files - ONLY extract changed functions
            task2 = progress.add_task("[cyan]Analyzing changed functions...", total=None)
            log_step("Phase 2", f"Extracting changed functions from {len(changed_files)} files")
            try:
                new_functions, new_interfaces = self._parse_only_changed_functions(changed_files)
                progress.update(task2, completed=True)
                console.print(f"✓ Found {len(new_functions)} changed functions, {len(new_interfaces)} interfaces")
                for f in new_functions[:5]:  # Show first 5
                    log_step("  -", f"Function: {f.name} in {f.file_path}")
            except Exception as e:
                progress.update(task2, completed=True)
                console.print(f"[red]✗ Function extraction failed: {e}[/red]")
                traceback.print_exc()
                raise

            # Phase 3: Parse old versions for signature comparison
            task3 = progress.add_task("[cyan]Detecting signature changes...", total=None)
            log_step("Phase 3", "Comparing signatures between old and new versions")
            try:
                old_functions, old_interfaces = self._parse_old_versions(changed_files)
                signature_changes = detect_signature_changes(old_functions, new_functions)
                progress.update(task3, completed=True)
                console.print(f"✓ Found {len(signature_changes)} signature changes")
                for sc in signature_changes:
                    log_step("  -", f"{sc.function_name}: {sc.change_type} ({sc.risk_level})")
            except Exception as e:
                progress.update(task3, completed=True)
                console.print(f"[red]✗ Signature detection failed: {e}[/red]")
                traceback.print_exc()
                raise

            # Phase 4: Build call graph (only for changed functions)
            # Skip for large MRs (>100 functions) as it's too slow
            MAX_FUNCTIONS_FOR_GRAPH = 100

            if len(new_functions) <= MAX_FUNCTIONS_FOR_GRAPH:
                task4 = progress.add_task("[cyan]Building call graph...", total=None)
                log_step("Phase 4", f"Building call graph for {len(new_functions)} functions")
                try:
                    call_graph = build_call_graph(self.repo_path, new_functions)
                    progress.update(task4, completed=True)
                    console.print(f"✓ Built call graph with {len(call_graph.nodes)} nodes")
                    for name, node in list(call_graph.nodes.items())[:3]:  # Show first 3
                        log_step("  -", f"{name}: calls {len(node.calls)}, called by {len(node.called_by)}")
                except Exception as e:
                    progress.update(task4, completed=True)
                    console.print(f"[yellow]⚠ Call graph building failed: {e}[/yellow]")
                    console.print("[yellow]Continuing without call graph...[/yellow]")
                    call_graph = CallGraph()  # Empty graph
            else:
                console.print(f"[yellow]⚠ Skipping call graph ({len(new_functions)} functions > {MAX_FUNCTIONS_FOR_GRAPH} limit)[/yellow]")
                console.print(f"[dim]Large MRs have call graph disabled for performance[/dim]")
                call_graph = CallGraph()  # Empty graph

            # Phase 5: Find duplicates
            task5 = progress.add_task("[cyan]Detecting duplicates...", total=None)
            duplicates = find_duplicates(
                new_interfaces,
                old_interfaces,
                new_functions,
                old_functions
            )
            progress.update(task5, completed=True)
            console.print(f"✓ Found {len(duplicates)} potential duplicates")

            # Phase 6: Find related tests (simple heuristic)
            task6 = progress.add_task("[cyan]Finding test files...", total=None)
            related_tests = self._find_test_files(changed_files)
            progress.update(task6, completed=True)
            console.print(f"✓ Found {len(related_tests)} test files")

            # Phase 7: Package context
            task7 = progress.add_task("[cyan]Packaging context...", total=None)
            context = ContextPacket(
                branch_name=branch_name,
                changed_files=changed_files,
                changed_functions=new_functions,
                signature_changes=signature_changes,
                call_graph=call_graph,
                duplicate_patterns=duplicates,
                related_tests=related_tests
            )
            context_markdown = package_context(context)
            progress.update(task7, completed=True)
            console.print(f"✓ Context packaged ({len(context_markdown)} chars)")

            # Phase 8: Generate review with LLM
            task8 = progress.add_task(f"[cyan]Generating review with {self.model}...", total=None)
            log_step("Phase 8", f"Sending {len(context_markdown)} chars to {self.model}")
            try:
                review = generate_review(context, context_markdown, self.model)
                progress.update(task8, completed=True)
                log_step("  -", f"Received {len(review)} chars from LLM")
            except Exception as e:
                progress.update(task8, completed=True)
                console.print(f"[red]✗ Review generation failed: {e}[/red]")
                traceback.print_exc()
                raise

        console.print("\n[bold green]✓ Review complete![/bold green]\n")
        return review

    def _parse_only_changed_functions(self, changed_files: List[FileDiff]) -> tuple[List[FunctionNode], List[InterfaceNode]]:
        """
        Parse ONLY functions that actually changed in the diff.

        This is the key optimization:
        - Extract which function names changed in each file
        - Only parse those specific functions
        - Ignore unchanged functions
        """
        all_functions = []
        all_interfaces = []

        for file_diff in changed_files:
            if not file_diff.new_content:
                continue

            try:
                # Find which functions changed in this file
                changed_func_names = get_changed_function_names(file_diff)

                if not changed_func_names:
                    # No function changes, skip
                    continue

                log_step("  ", f"{file_diff.path}: {len(changed_func_names)} functions changed")

                # Parse all functions in file
                functions, interfaces = parse_typescript_file(
                    file_diff.path,
                    file_diff.new_content
                )

                # Filter to only changed functions
                changed_functions = [
                    f for f in functions
                    if f.name in changed_func_names
                ]

                all_functions.extend(changed_functions)
                all_interfaces.extend(interfaces)  # Keep all interfaces

            except Exception as e:
                console.print(f"[yellow]Warning: Could not parse {file_diff.path}: {e}[/yellow]")

        return all_functions, all_interfaces

    def _parse_old_versions(self, changed_files: List[FileDiff]) -> tuple[List[FunctionNode], List[InterfaceNode]]:
        """Parse old versions of changed files (for comparison)."""
        all_functions = []
        all_interfaces = []

        for file_diff in changed_files:
            if file_diff.old_content:  # Only parse if file existed before
                try:
                    functions, interfaces = parse_typescript_file(
                        file_diff.path,
                        file_diff.old_content
                    )
                    all_functions.extend(functions)
                    all_interfaces.extend(interfaces)
                except Exception as e:
                    # Silently skip parsing errors for old versions
                    pass

        return all_functions, all_interfaces

    def _find_test_files(self, changed_files: List[FileDiff]) -> List[str]:
        """
        Find test files related to changed files.

        Simple heuristic: look for .test.ts, .spec.ts files with similar names.
        """
        test_files = []

        for file_diff in changed_files:
            # Generate possible test file names
            base_name = file_diff.path.replace('.ts', '').replace('.tsx', '')
            possible_tests = [
                f"{base_name}.test.ts",
                f"{base_name}.test.tsx",
                f"{base_name}.spec.ts",
                f"{base_name}.spec.tsx",
            ]

            for test_file in possible_tests:
                full_path = os.path.join(self.repo_path, test_file)
                if os.path.exists(full_path):
                    test_files.append(test_file)

        return test_files
