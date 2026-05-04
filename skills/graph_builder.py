"""Graph builder skill - build call graph for changed functions only."""

import os
import subprocess
from typing import List, Set, Dict
from core.models import FunctionNode, CallGraph, CallGraphNode
from skills.ast_parser import ASTParser


class GraphBuilder:
    """Build call graph for changed functions (lightweight approach)."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.ast_parser = ASTParser()

    def build_graph(self, changed_functions: List[FunctionNode]) -> CallGraph:
        """
        Build call graph for changed functions.

        Only analyzes:
        - Who calls these functions (callers)
        - What these functions call (callees)

        Does NOT build full repository graph.
        """
        graph = CallGraph()

        # Extract function names
        changed_func_names = {f.name for f in changed_functions}

        for func in changed_functions:
            # Create node
            node = CallGraphNode(function=func)

            # Find who calls this function (using grep)
            node.called_by = self._find_callers(func.name)

            # Find what this function calls
            # Read the function's file to analyze its calls
            try:
                with open(os.path.join(self.repo_path, func.file_path), 'r') as f:
                    content = f.read()
                    # Extract just this function's body
                    func_body = content[func.start_byte:func.end_byte]
                    node.calls = self._extract_function_calls(func_body)
            except Exception as e:
                print(f"Error reading {func.file_path}: {e}")

            graph.add_node(node)

        return graph

    def _find_callers(self, function_name: str) -> List[str]:
        """
        Find files that call this function using ripgrep/grep.

        Returns list of file paths.
        """
        try:
            # Try ripgrep first (much faster)
            result = subprocess.run(
                ['rg', f'{function_name}\\(', self.repo_path,
                 '--type', 'ts', '--type', 'js',
                 '--files-with-matches'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                return [f for f in files if f]

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to grep
            try:
                result = subprocess.run(
                    ['grep', '-r', '-l', f'{function_name}(',
                     '--include=*.ts', '--include=*.tsx',
                     '--include=*.js', '--include=*.jsx',
                     self.repo_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    files = result.stdout.strip().split('\n')
                    return [f for f in files if f]

            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        return []

    def _extract_function_calls(self, code: str) -> List[str]:
        """
        Extract function calls from code.

        Returns list of function names being called.
        """
        calls = []

        # Simple regex-based extraction (faster than full AST)
        import re
        # Match function calls: functionName(
        pattern = r'\b([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\('
        matches = re.findall(pattern, code)

        # Filter out common keywords
        keywords = {
            'if', 'for', 'while', 'switch', 'catch', 'function',
            'return', 'typeof', 'instanceof', 'new', 'delete'
        }

        calls = [m for m in matches if m not in keywords]

        return list(set(calls))  # Deduplicate


def build_call_graph(repo_path: str, changed_functions: List[FunctionNode]) -> CallGraph:
    """Build call graph for changed functions."""
    builder = GraphBuilder(repo_path)
    return builder.build_graph(changed_functions)
