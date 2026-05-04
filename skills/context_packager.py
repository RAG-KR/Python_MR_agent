"""Context packaging skill - prepare context for LLM."""

from core.models import ContextPacket, RiskLevel


class ContextPackager:
    """Package context into markdown for LLM consumption."""

    def to_markdown(self, context: ContextPacket) -> str:
        """
        Convert context packet to markdown.

        Optimized to reduce hallucination:
        - Clear function names
        - Explicit dependencies
        - No line numbers (use function names + file paths)
        """
        sections = []

        # Summary
        sections.append(self._format_summary(context))

        # Changed functions
        if context.changed_functions:
            sections.append(self._format_changed_functions(context))

        # Signature changes (CRITICAL - put early)
        if context.signature_changes:
            sections.append(self._format_signature_changes(context))

        # Call graph
        if context.call_graph.nodes:
            sections.append(self._format_call_graph(context))

        # Duplicate patterns
        if context.duplicate_patterns:
            sections.append(self._format_duplicates(context))

        # Test files
        if context.related_tests:
            sections.append(self._format_tests(context))

        # Git diff summary
        sections.append(self._format_diff_summary(context))

        return "\n\n".join(sections)

    def _format_summary(self, context: ContextPacket) -> str:
        """Format summary section."""
        blocker_count = sum(
            1 for s in context.signature_changes
            if s.risk_level == RiskLevel.BLOCKER
        )

        return f"""# MR Review Context

## Summary
- Branch: `{context.branch_name}`
- Files changed: {len(context.changed_files)}
- Functions modified: {len(context.changed_functions)}
- Signature changes: {len(context.signature_changes)} ({blocker_count} BLOCKER)
- Duplicate patterns found: {len(context.duplicate_patterns)}"""

    def _format_changed_functions(self, context: ContextPacket) -> str:
        """Format changed functions section."""
        lines = ["## Changed Functions\n"]

        for func in context.changed_functions:
            lines.append(f"### {func.name}()")
            lines.append(f"**File:** `{func.file_path}`")
            lines.append(f"**Signature:** `{func.signature}`")
            lines.append(f"**Hash:** `{func.body_hash[:12]}...`")

            if func.parent_class:
                lines.append(f"**Class:** `{func.parent_class}`")

            if func.decorators:
                lines.append(f"**Decorators:** {', '.join(func.decorators)}")

            # Add call info from graph
            if func.name in context.call_graph.nodes:
                node = context.call_graph.nodes[func.name]

                if node.calls:
                    lines.append(f"**Calls:** {', '.join(node.calls[:10])}")  # First 10

                if node.called_by:
                    lines.append(f"**Called by:** {len(node.called_by)} file(s)")

            lines.append("")  # Blank line

        return "\n".join(lines)

    def _format_signature_changes(self, context: ContextPacket) -> str:
        """Format signature changes section (CRITICAL)."""
        lines = ["## Signature Changes (CRITICAL)\n"]

        for change in context.signature_changes:
            risk_emoji = "🔴" if change.risk_level == RiskLevel.BLOCKER else "🟡"
            lines.append(f"### {risk_emoji} {change.function_name}() - {change.risk_level}")
            lines.append(f"**File:** `{change.file_path}`")
            lines.append(f"**Change Type:** {change.change_type}")
            lines.append(f"**Old:** `{change.old_signature}`")
            lines.append(f"**New:** `{change.new_signature}`")

            # Find callers from graph
            if change.function_name in context.call_graph.nodes:
                callers = context.call_graph.nodes[change.function_name].called_by
                if callers:
                    lines.append(f"**⚠️ Must verify {len(callers)} caller(s) match new signature:**")
                    for caller in callers[:5]:  # Show first 5
                        lines.append(f"  - {caller}")
                    if len(callers) > 5:
                        lines.append(f"  - ...and {len(callers) - 5} more")

            lines.append("")

        return "\n".join(lines)

    def _format_call_graph(self, context: ContextPacket) -> str:
        """Format call graph section."""
        lines = ["## Call Graph\n"]

        for func_name, node in context.call_graph.nodes.items():
            if node.calls or node.called_by:
                lines.append(f"### {func_name}()")

                if node.calls:
                    lines.append(f"**Calls:** {', '.join(node.calls[:10])}")

                if node.called_by:
                    lines.append(f"**Called by:** {len(node.called_by)} file(s)")
                    for caller in node.called_by[:3]:
                        lines.append(f"  - {caller}")

                lines.append("")

        return "\n".join(lines)

    def _format_duplicates(self, context: ContextPacket) -> str:
        """Format duplicate patterns section."""
        lines = ["## Duplicate Patterns Detected\n"]

        for dup in context.duplicate_patterns:
            lines.append(f"### {dup.type.replace('_', ' ').title()}")
            lines.append(f"**New:** `{dup.duplicate_name}` in `{dup.duplicate_file}`")
            lines.append(f"**Existing:** `{dup.original_name}` in `{dup.original_file}`")
            lines.append(f"**Similarity:** {dup.similarity_score:.0%}")
            lines.append(f"**Reason:** {dup.reason}")
            lines.append(f"**⚠️ Recommendation:** Consider reusing `{dup.original_name}` instead")
            lines.append("")

        return "\n".join(lines)

    def _format_tests(self, context: ContextPacket) -> str:
        """Format test coverage section."""
        lines = ["## Related Test Files\n"]

        for test in context.related_tests:
            lines.append(f"- `{test}`")

        return "\n".join(lines)

    def _format_diff_summary(self, context: ContextPacket) -> str:
        """Format git diff summary."""
        lines = ["## Changed Files\n"]

        for file_diff in context.changed_files:
            lines.append(f"- `{file_diff.path}` ({file_diff.change_type})")

        return "\n".join(lines)


def package_context(context: ContextPacket) -> str:
    """Package context into markdown for LLM."""
    packager = ContextPackager()
    return packager.to_markdown(context)
