"""Diff analyzer - extract only changed functions from git diff."""

import re
from typing import List, Set, Tuple
from core.models import FileDiff


class DiffAnalyzer:
    """Analyze git diff to find which functions actually changed."""

    def extract_changed_function_names(self, file_diff: FileDiff) -> Set[str]:
        """
        Extract names of functions that actually changed.

        Returns set of function names that have modifications.
        """
        if not file_diff.new_content:
            return set()

        changed_lines = self._get_changed_line_numbers(file_diff)
        function_ranges = self._extract_function_ranges(file_diff.new_content)

        # Find which functions contain changed lines
        changed_functions = set()
        for func_name, (start_line, end_line) in function_ranges.items():
            # Check if any changed line falls within this function
            for changed_line in changed_lines:
                if start_line <= changed_line <= end_line:
                    changed_functions.add(func_name)
                    break

        return changed_functions

    def _get_changed_line_numbers(self, file_diff: FileDiff) -> Set[int]:
        """
        Get line numbers that actually changed in the diff.

        This is a simple heuristic - compares old and new content line by line.
        """
        if not file_diff.old_content or not file_diff.new_content:
            # File added or deleted - all lines changed
            return set(range(1, file_diff.new_content.count('\n') + 2))

        old_lines = file_diff.old_content.split('\n')
        new_lines = file_diff.new_content.split('\n')

        changed = set()

        # Simple line-by-line comparison (could use difflib for better accuracy)
        for i, (old, new) in enumerate(zip(old_lines, new_lines), start=1):
            if old != new:
                changed.add(i)

        # If new file has more lines
        if len(new_lines) > len(old_lines):
            for i in range(len(old_lines) + 1, len(new_lines) + 1):
                changed.add(i)

        return changed

    def _extract_function_ranges(self, content: str) -> dict[str, Tuple[int, int]]:
        """
        Extract function names and their line ranges (start, end).

        Uses simple regex - fast but not perfect.
        Better than parsing all functions with tree-sitter.
        """
        functions = {}
        lines = content.split('\n')

        # Patterns for function declarations
        patterns = [
            r'^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)',  # function foo()
            r'^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=]+)\s*=>',  # const foo = () =>
            r'^\s*(?:public|private|protected)?\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*{',  # class methods
        ]

        for i, line in enumerate(lines, start=1):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    func_name = match.group(1)

                    # Find end of function (simple brace counting)
                    end_line = self._find_function_end(lines, i - 1)
                    functions[func_name] = (i, end_line)
                    break

        return functions

    def _find_function_end(self, lines: List[str], start_idx: int) -> int:
        """
        Find where a function ends by counting braces.

        Simple heuristic - not perfect but fast.
        """
        brace_count = 0
        started = False

        for i in range(start_idx, len(lines)):
            line = lines[i]

            # Count braces
            for char in line:
                if char == '{':
                    brace_count += 1
                    started = True
                elif char == '}':
                    brace_count -= 1

                    # Function ended
                    if started and brace_count == 0:
                        return i + 1

        # Couldn't find end, return a reasonable guess
        return min(start_idx + 50, len(lines))


def get_changed_function_names(file_diff: FileDiff) -> Set[str]:
    """Extract function names that actually changed in this file."""
    analyzer = DiffAnalyzer()
    return analyzer.extract_changed_function_names(file_diff)
