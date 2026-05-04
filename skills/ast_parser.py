"""AST parsing skill using tree-sitter for TypeScript/JavaScript."""

import hashlib
from typing import List, Dict, Optional, Set
from tree_sitter import Language, Parser, Node
import tree_sitter_typescript as tstypescript
from core.models import FunctionNode, InterfaceNode, Signature, Parameter


class ASTParser:
    """Fast AST parser using tree-sitter."""

    def __init__(self):
        # Load TypeScript grammar
        self.ts_language = Language(tstypescript.language_typescript())
        self.tsx_language = Language(tstypescript.language_tsx())

    def parse_file(self, file_path: str, content: str) -> tuple[List[FunctionNode], List[InterfaceNode]]:
        """
        Parse a TypeScript/JavaScript file.

        Returns:
            Tuple of (functions, interfaces)
        """
        # Create parser with appropriate language
        parser = Parser(self.tsx_language if file_path.endswith(('.tsx', '.jsx')) else self.ts_language)

        # Parse the file
        tree = parser.parse(bytes(content, "utf8"))
        root_node = tree.root_node

        # Extract functions and interfaces
        functions = self._extract_functions(root_node, content, file_path)
        interfaces = self._extract_interfaces(root_node, content, file_path)

        return functions, interfaces

    def _extract_functions(self, root: Node, content: str, file_path: str) -> List[FunctionNode]:
        """Extract all function definitions."""
        functions = []

        # Query for different function types
        function_types = [
            'function_declaration',
            'method_definition',
            'arrow_function',
            'function_expression'
        ]

        for node in self._walk_tree(root):
            if node.type in function_types:
                func = self._parse_function_node(node, content, file_path)
                if func and func.name:  # Only add named functions
                    functions.append(func)

        return functions

    def _extract_interfaces(self, root: Node, content: str, file_path: str) -> List[InterfaceNode]:
        """Extract all interface definitions."""
        interfaces = []

        for node in self._walk_tree(root):
            if node.type == 'interface_declaration':
                interface = self._parse_interface_node(node, content, file_path)
                if interface:
                    interfaces.append(interface)

        return interfaces

    def _parse_function_node(self, node: Node, content: str, file_path: str) -> Optional[FunctionNode]:
        """Parse a single function node."""
        try:
            # Get function name
            name = self._get_function_name(node, content)
            if not name:
                return None

            # Get signature
            signature = self._parse_signature(node, content)

            # Get function body and hash it
            body = self._get_node_text(node, content)
            body_hash = hashlib.sha256(body.encode()).hexdigest()

            # Get parent class if it's a method
            parent_class = self._get_parent_class(node, content)

            # Get decorators
            decorators = self._get_decorators(node, content)

            return FunctionNode(
                name=name,
                file_path=file_path,
                signature=signature,
                body_hash=body_hash,
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                parent_class=parent_class,
                decorators=decorators
            )
        except Exception as e:
            print(f"Error parsing function: {e}")
            return None

    def _parse_interface_node(self, node: Node, content: str, file_path: str) -> Optional[InterfaceNode]:
        """Parse a single interface node."""
        try:
            # Get interface name
            name_node = node.child_by_field_name('name')
            if not name_node:
                return None
            name = self._get_node_text(name_node, content)

            # Get properties
            properties = {}
            body_node = node.child_by_field_name('body')
            if body_node:
                for child in body_node.children:
                    if child.type == 'property_signature':
                        prop_name, prop_type = self._parse_property(child, content)
                        if prop_name:
                            properties[prop_name] = prop_type

            # Hash the interface definition
            interface_text = self._get_node_text(node, content)
            interface_hash = hashlib.sha256(interface_text.encode()).hexdigest()

            # Get extended interfaces
            extends = self._get_extends(node, content)

            return InterfaceNode(
                name=name,
                file_path=file_path,
                properties=properties,
                hash=interface_hash,
                extends=extends
            )
        except Exception as e:
            print(f"Error parsing interface: {e}")
            return None

    def _get_function_name(self, node: Node, content: str) -> Optional[str]:
        """Extract function name from node."""
        # Try different name fields
        name_node = (
            node.child_by_field_name('name') or
            node.child_by_field_name('property')
        )

        if name_node:
            return self._get_node_text(name_node, content)

        # For arrow functions assigned to variables
        parent = node.parent
        if parent and parent.type == 'variable_declarator':
            name_node = parent.child_by_field_name('name')
            if name_node:
                return self._get_node_text(name_node, content)

        return None

    def _parse_signature(self, node: Node, content: str) -> Signature:
        """Parse function signature."""
        parameters = []
        return_type = "void"

        # Get parameters
        params_node = node.child_by_field_name('parameters')
        if params_node:
            for param_node in params_node.children:
                if param_node.type in ['required_parameter', 'optional_parameter']:
                    param = self._parse_parameter(param_node, content)
                    if param:
                        parameters.append(param)

        # Get return type
        return_type_node = node.child_by_field_name('return_type')
        if return_type_node:
            # Skip the ':' token
            for child in return_type_node.children:
                if child.type != ':':
                    return_type = self._get_node_text(child, content)
                    break

        return Signature(parameters=parameters, return_type=return_type)

    def _parse_parameter(self, node: Node, content: str) -> Optional[Parameter]:
        """Parse a function parameter."""
        try:
            name_node = node.child_by_field_name('pattern')
            if not name_node:
                return None

            name = self._get_node_text(name_node, content)
            optional = node.type == 'optional_parameter'

            # Get type annotation
            type_annotation = "any"
            type_node = node.child_by_field_name('type')
            if type_node:
                # Skip the ':' token
                for child in type_node.children:
                    if child.type != ':':
                        type_annotation = self._get_node_text(child, content)
                        break

            return Parameter(name=name, type=type_annotation, optional=optional)
        except Exception:
            return None

    def _parse_property(self, node: Node, content: str) -> tuple[Optional[str], str]:
        """Parse interface property."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return None, "any"

        name = self._get_node_text(name_node, content)

        type_node = node.child_by_field_name('type')
        if type_node:
            # Skip the ':' token
            for child in type_node.children:
                if child.type != ':':
                    return name, self._get_node_text(child, content)

        return name, "any"

    def _get_parent_class(self, node: Node, content: str) -> Optional[str]:
        """Get parent class name if this is a method."""
        parent = node.parent
        while parent:
            if parent.type == 'class_declaration':
                name_node = parent.child_by_field_name('name')
                if name_node:
                    return self._get_node_text(name_node, content)
            parent = parent.parent
        return None

    def _get_decorators(self, node: Node, content: str) -> List[str]:
        """Get decorators for a function/method."""
        decorators = []
        # Look for decorator nodes before this node
        parent = node.parent
        if parent:
            for child in parent.children:
                if child.type == 'decorator':
                    decorators.append(self._get_node_text(child, content))
        return decorators

    def _get_extends(self, node: Node, content: str) -> List[str]:
        """Get list of interfaces this interface extends."""
        extends = []
        heritage_node = node.child_by_field_name('heritage')
        if heritage_node:
            for child in heritage_node.children:
                if child.type == 'type_identifier':
                    extends.append(self._get_node_text(child, content))
        return extends

    def _walk_tree(self, node: Node):
        """Walk the tree depth-first."""
        yield node
        for child in node.children:
            yield from self._walk_tree(child)

    def _get_node_text(self, node: Node, content: str) -> str:
        """Get text for a node."""
        return content[node.start_byte:node.end_byte]

    def extract_imports(self, content: str, file_path: str = "file.ts") -> List[str]:
        """Extract all import statements from file."""
        parser = Parser(self.ts_language)
        tree = parser.parse(bytes(content, "utf8"))
        imports = []

        for node in self._walk_tree(tree.root_node):
            if node.type == 'import_statement':
                imports.append(self._get_node_text(node, content))

        return imports

    def find_function_calls(self, content: str, function_names: Set[str], file_path: str = "file.ts") -> Dict[str, List[str]]:
        """
        Find which functions from function_names are called in this file.

        Returns:
            Dict mapping function_name -> list of locations where it's called
        """
        parser = Parser(self.ts_language)
        tree = parser.parse(bytes(content, "utf8"))
        calls = {name: [] for name in function_names}

        for node in self._walk_tree(tree.root_node):
            if node.type == 'call_expression':
                # Get the function being called
                function_node = node.child_by_field_name('function')
                if function_node:
                    func_name = self._get_node_text(function_node, content)
                    # Handle method calls (obj.method)
                    if '.' in func_name:
                        func_name = func_name.split('.')[-1]

                    if func_name in function_names:
                        calls[func_name].append(f"{node.start_point[0]}:{node.start_point[1]}")

        return {k: v for k, v in calls.items() if v}  # Only return functions that were called


def parse_typescript_file(file_path: str, content: str) -> tuple[List[FunctionNode], List[InterfaceNode]]:
    """
    Parse a TypeScript/JavaScript file.

    Returns:
        Tuple of (functions, interfaces)
    """
    parser = ASTParser()
    return parser.parse_file(file_path, content)
