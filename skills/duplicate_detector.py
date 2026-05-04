"""Duplicate detection skill - find similar interfaces and code."""

from typing import List
from core.models import InterfaceNode, FunctionNode, DuplicatePattern


class DuplicateDetector:
    """Detect duplicate interfaces and similar code patterns."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold

    def find_duplicate_interfaces(
        self,
        new_interfaces: List[InterfaceNode],
        existing_interfaces: List[InterfaceNode]
    ) -> List[DuplicatePattern]:
        """
        Find duplicate or similar interfaces.

        Checks:
        1. Exact match (same hash)
        2. Structural similarity (same properties)
        """
        duplicates = []

        for new_interface in new_interfaces:
            for existing in existing_interfaces:
                # Skip if same file (not a duplicate, just same interface)
                if new_interface.file_path == existing.file_path:
                    continue

                # Check for exact match
                if new_interface.hash == existing.hash:
                    duplicates.append(DuplicatePattern(
                        type='identical_interface',
                        original_name=existing.name,
                        original_file=existing.file_path,
                        duplicate_name=new_interface.name,
                        duplicate_file=new_interface.file_path,
                        similarity_score=1.0,
                        reason=f"Identical interface definition"
                    ))
                    continue

                # Check structural similarity
                similarity = self._calculate_interface_similarity(
                    new_interface,
                    existing
                )

                if similarity >= self.similarity_threshold:
                    duplicates.append(DuplicatePattern(
                        type='similar_interface',
                        original_name=existing.name,
                        original_file=existing.file_path,
                        duplicate_name=new_interface.name,
                        duplicate_file=new_interface.file_path,
                        similarity_score=similarity,
                        reason=self._explain_similarity(new_interface, existing)
                    ))

        return duplicates

    def find_duplicate_code(
        self,
        new_functions: List[FunctionNode],
        existing_functions: List[FunctionNode]
    ) -> List[DuplicatePattern]:
        """
        Find duplicate code blocks.

        Checks:
        1. Exact hash match
        """
        duplicates = []

        for new_func in new_functions:
            for existing in existing_functions:
                # Skip if same file and name (same function)
                if (new_func.file_path == existing.file_path and
                    new_func.name == existing.name):
                    continue

                # Check for exact code match
                if new_func.body_hash == existing.body_hash:
                    duplicates.append(DuplicatePattern(
                        type='duplicate_code',
                        original_name=existing.name,
                        original_file=existing.file_path,
                        duplicate_name=new_func.name,
                        duplicate_file=new_func.file_path,
                        similarity_score=1.0,
                        reason=f"Identical function implementation"
                    ))

        return duplicates

    def _calculate_interface_similarity(
        self,
        interface1: InterfaceNode,
        interface2: InterfaceNode
    ) -> float:
        """
        Calculate similarity between two interfaces.

        Based on:
        - Number of common properties
        - Property type matches
        """
        props1 = set(interface1.properties.keys())
        props2 = set(interface2.properties.keys())

        if not props1 and not props2:
            return 0.0

        # Jaccard similarity for property names
        intersection = props1 & props2
        union = props1 | props2

        if not union:
            return 0.0

        name_similarity = len(intersection) / len(union)

        # Check type matches for common properties
        type_matches = 0
        for prop in intersection:
            if interface1.properties[prop] == interface2.properties[prop]:
                type_matches += 1

        if intersection:
            type_similarity = type_matches / len(intersection)
        else:
            type_similarity = 0.0

        # Combined score (weighted average)
        return 0.6 * name_similarity + 0.4 * type_similarity

    def _explain_similarity(
        self,
        interface1: InterfaceNode,
        interface2: InterfaceNode
    ) -> str:
        """Generate human-readable explanation of similarity."""
        common_props = set(interface1.properties.keys()) & set(interface2.properties.keys())

        if len(common_props) > 0:
            props_str = ", ".join(sorted(common_props)[:5])  # First 5
            if len(common_props) > 5:
                props_str += f", and {len(common_props) - 5} more"
            return f"Both interfaces have common properties: {props_str}"

        return "Interfaces have similar structure"


def find_duplicates(
    new_interfaces: List[InterfaceNode],
    existing_interfaces: List[InterfaceNode],
    new_functions: List[FunctionNode],
    existing_functions: List[FunctionNode],
    similarity_threshold: float = 0.85
) -> List[DuplicatePattern]:
    """Find duplicate interfaces and code."""
    detector = DuplicateDetector(similarity_threshold)

    interface_duplicates = detector.find_duplicate_interfaces(
        new_interfaces,
        existing_interfaces
    )

    code_duplicates = detector.find_duplicate_code(
        new_functions,
        existing_functions
    )

    return interface_duplicates + code_duplicates
