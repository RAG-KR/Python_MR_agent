"""Core data models for MR review agent."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class ChangeType(str, Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


class RiskLevel(str, Enum):
    BLOCKER = "BLOCKER"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Parameter:
    """Function parameter with type information."""
    name: str
    type: str
    optional: bool = False
    default_value: Optional[str] = None


@dataclass
class Signature:
    """Function signature."""
    parameters: List[Parameter] = field(default_factory=list)
    return_type: str = "void"

    def __str__(self) -> str:
        params = ", ".join([
            f"{p.name}: {p.type}" + ("?" if p.optional else "")
            for p in self.parameters
        ])
        return f"({params}) => {self.return_type}"


@dataclass
class FunctionNode:
    """Represents a function in the codebase."""
    name: str
    file_path: str
    signature: Signature
    body_hash: str  # SHA256 of function body
    start_byte: int
    end_byte: int
    parent_class: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)  # Imports used in this function

    def get_id(self) -> str:
        """Generate stable identifier (not line-based)."""
        return f"{self.body_hash[:8]}_{self.name}@{self.file_path}"


@dataclass
class InterfaceNode:
    """Represents a TypeScript interface."""
    name: str
    file_path: str
    properties: Dict[str, str]  # property_name -> type
    hash: str  # SHA256 of interface definition
    extends: List[str] = field(default_factory=list)


@dataclass
class FileDiff:
    """Git diff for a single file."""
    path: str
    change_type: ChangeType
    old_content: Optional[str] = None
    new_content: Optional[str] = None


@dataclass
class SignatureChange:
    """Detected signature change."""
    function_name: str
    file_path: str
    old_signature: Signature
    new_signature: Signature
    change_type: str  # 'param_added', 'param_removed', 'type_changed', 'return_changed'
    risk_level: RiskLevel


@dataclass
class CallGraphNode:
    """Node in the call graph."""
    function: FunctionNode
    calls: List[str] = field(default_factory=list)  # Function names this calls
    called_by: List[str] = field(default_factory=list)  # Functions that call this


@dataclass
class CallGraph:
    """Call graph for changed functions."""
    nodes: Dict[str, CallGraphNode] = field(default_factory=dict)

    def add_node(self, node: CallGraphNode):
        """Add a node to the graph."""
        self.nodes[node.function.name] = node

    def find_callers(self, function_name: str) -> List[str]:
        """Find all functions that call this one."""
        node = self.nodes.get(function_name)
        return node.called_by if node else []

    def find_callees(self, function_name: str) -> List[str]:
        """Find all functions this one calls."""
        node = self.nodes.get(function_name)
        return node.calls if node else []


@dataclass
class DuplicatePattern:
    """Detected duplicate code/interface."""
    type: str  # 'duplicate_interface', 'duplicate_code', 'similar_code'
    original_name: str
    original_file: str
    duplicate_name: str
    duplicate_file: str
    similarity_score: float
    reason: str


@dataclass
class ContextPacket:
    """All context for LLM review."""
    branch_name: str
    changed_files: List[FileDiff]
    changed_functions: List[FunctionNode]
    signature_changes: List[SignatureChange]
    call_graph: CallGraph
    duplicate_patterns: List[DuplicatePattern]
    related_tests: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """Generate summary string."""
        return (
            f"Branch: {self.branch_name}\n"
            f"Files changed: {len(self.changed_files)}\n"
            f"Functions modified: {len(self.changed_functions)}\n"
            f"Signature changes: {len(self.signature_changes)} "
            f"({sum(1 for s in self.signature_changes if s.risk_level == RiskLevel.BLOCKER)} BLOCKER)"
        )


@dataclass
class ReviewComment:
    """Single review comment."""
    title: str
    function_name: str
    current_code: Optional[str] = None
    suggested_fix: Optional[str] = None
    impact: str = ""


@dataclass
class Decision:
    """Final review decision."""
    status: str  # 'APPROVED' or 'COMMENTS_TO_ADDRESS'
    risk_level: str  # 'LOW', 'MEDIUM', 'HIGH'
    reason: str


@dataclass
class ReviewReport:
    """Complete review report."""
    summary: str
    blockers: List[ReviewComment] = field(default_factory=list)
    should_fix: List[ReviewComment] = field(default_factory=list)
    future_concerns: List[str] = field(default_factory=list)
    code_quality_notes: List[str] = field(default_factory=list)
    positive_feedback: List[str] = field(default_factory=list)
    final_decision: Optional[Decision] = None
