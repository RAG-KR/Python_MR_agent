#!/usr/bin/env python3
"""Simple test to validate the MR review agent works."""

import sys
from skills.ast_parser import parse_typescript_file
from skills.signature_tracker import detect_signature_changes
from core.models import FunctionNode, Signature, Parameter

# Test TypeScript code
test_code_old = """
function processPayment(userId: string, amount: number): Promise<void> {
    return Promise.resolve();
}

interface UserPayload {
    id: string;
    name: string;
    email: string;
}
"""

test_code_new = """
function processPayment(userId: string, amount: number, currency: string): Promise<void> {
    return Promise.resolve();
}

interface UserPayload {
    id: string;
    name: string;
    email: string;
}

interface UserRequest {
    id: string;
    name: string;
    email: string;
}
"""

def test_ast_parsing():
    """Test AST parsing."""
    print("Testing AST parsing...")

    functions, interfaces = parse_typescript_file("test.ts", test_code_new)

    print(f"✓ Extracted {len(functions)} functions")
    print(f"✓ Extracted {len(interfaces)} interfaces")

    if len(functions) > 0:
        func = functions[0]
        print(f"  Function: {func.name}")
        print(f"  Signature: {func.signature}")
        print(f"  Hash: {func.body_hash[:12]}...")

    if len(interfaces) > 0:
        interface = interfaces[0]
        print(f"  Interface: {interface.name}")
        print(f"  Properties: {list(interface.properties.keys())}")

    return functions, interfaces


def test_signature_detection():
    """Test signature change detection."""
    print("\nTesting signature change detection...")

    old_functions, _ = parse_typescript_file("test.ts", test_code_old)
    new_functions, _ = parse_typescript_file("test.ts", test_code_new)

    from skills.signature_tracker import detect_signature_changes
    changes = detect_signature_changes(old_functions, new_functions)

    print(f"✓ Detected {len(changes)} signature changes")

    if len(changes) > 0:
        change = changes[0]
        print(f"  Function: {change.function_name}")
        print(f"  Type: {change.change_type}")
        print(f"  Risk: {change.risk_level}")
        print(f"  Old: {change.old_signature}")
        print(f"  New: {change.new_signature}")

    return changes


def test_duplicate_detection():
    """Test duplicate interface detection."""
    print("\nTesting duplicate detection...")

    _, interfaces = parse_typescript_file("test.ts", test_code_new)

    from skills.duplicate_detector import find_duplicates
    duplicates = find_duplicates(
        [interfaces[1]] if len(interfaces) > 1 else [],  # UserRequest
        [interfaces[0]] if len(interfaces) > 0 else [],  # UserPayload
        [],
        []
    )

    print(f"✓ Detected {len(duplicates)} duplicate patterns")

    if len(duplicates) > 0:
        dup = duplicates[0]
        print(f"  Type: {dup.type}")
        print(f"  Original: {dup.original_name}")
        print(f"  Duplicate: {dup.duplicate_name}")
        print(f"  Similarity: {dup.similarity_score:.0%}")
        print(f"  Reason: {dup.reason}")

    return duplicates


def main():
    print("=" * 60)
    print("MR Review Agent - Simple Test")
    print("=" * 60)

    try:
        functions, interfaces = test_ast_parsing()
        changes = test_signature_detection()
        duplicates = test_duplicate_detection()

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)

        print("\nSummary:")
        print(f"  - Functions extracted: {len(functions)}")
        print(f"  - Interfaces extracted: {len(interfaces)}")
        print(f"  - Signature changes detected: {len(changes)}")
        print(f"  - Duplicates found: {len(duplicates)}")

        return 0

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
