"""Signature tracking skill - detect breaking changes in function signatures."""

from typing import List, Dict
from core.models import FunctionNode, SignatureChange, Signature, RiskLevel


class SignatureTracker:
    """Track and detect function signature changes."""

    def detect_changes(
        self,
        old_functions: List[FunctionNode],
        new_functions: List[FunctionNode]
    ) -> List[SignatureChange]:
        """
        Detect signature changes between old and new versions.

        Returns list of SignatureChange objects with risk assessment.
        """
        changes = []

        # Create lookup for old functions
        old_funcs_map: Dict[str, FunctionNode] = {
            f.name: f for f in old_functions
        }

        # Compare each new function with its old version
        for new_func in new_functions:
            if new_func.name in old_funcs_map:
                old_func = old_funcs_map[new_func.name]
                change = self._compare_signatures(old_func, new_func)
                if change:
                    changes.append(change)

        return changes

    def _compare_signatures(
        self,
        old_func: FunctionNode,
        new_func: FunctionNode
    ) -> SignatureChange | None:
        """Compare two function signatures and detect changes."""
        old_sig = old_func.signature
        new_sig = new_func.signature

        # Check for parameter changes
        param_change = self._check_parameter_changes(old_sig, new_sig)
        if param_change:
            return SignatureChange(
                function_name=new_func.name,
                file_path=new_func.file_path,
                old_signature=old_sig,
                new_signature=new_sig,
                change_type=param_change['type'],
                risk_level=param_change['risk']
            )

        # Check for return type changes
        if old_sig.return_type != new_sig.return_type:
            # Return type change is usually a warning, not blocker
            return SignatureChange(
                function_name=new_func.name,
                file_path=new_func.file_path,
                old_signature=old_sig,
                new_signature=new_sig,
                change_type='return_type_changed',
                risk_level=RiskLevel.WARNING
            )

        return None

    def _check_parameter_changes(
        self,
        old_sig: Signature,
        new_sig: Signature
    ) -> Dict[str, any] | None:
        """
        Check for parameter changes.

        BLOCKER cases:
        - Required parameter added
        - Parameter removed (required or optional)
        - Parameter type changed
        - Optional parameter became required

        WARNING cases:
        - Optional parameter added
        """
        old_params = {p.name: p for p in old_sig.parameters}
        new_params = {p.name: p for p in new_sig.parameters}

        old_names = set(old_params.keys())
        new_names = set(new_params.keys())

        # Check for added parameters
        added_params = new_names - old_names
        if added_params:
            for param_name in added_params:
                param = new_params[param_name]
                if not param.optional:
                    return {
                        'type': 'param_added',
                        'risk': RiskLevel.BLOCKER
                    }
            # Only optional params added
            return {
                'type': 'param_added',
                'risk': RiskLevel.WARNING
            }

        # Check for removed parameters
        removed_params = old_names - new_names
        if removed_params:
            return {
                'type': 'param_removed',
                'risk': RiskLevel.BLOCKER
            }

        # Check for type changes
        for param_name in old_names & new_names:
            old_param = old_params[param_name]
            new_param = new_params[param_name]

            if old_param.type != new_param.type:
                return {
                    'type': 'param_type_changed',
                    'risk': RiskLevel.BLOCKER
                }

            # Check if optional changed
            if old_param.optional and not new_param.optional:
                return {
                    'type': 'param_became_required',
                    'risk': RiskLevel.BLOCKER
                }

        return None


def detect_signature_changes(
    old_functions: List[FunctionNode],
    new_functions: List[FunctionNode]
) -> List[SignatureChange]:
    """Detect signature changes between old and new functions."""
    tracker = SignatureTracker()
    return tracker.detect_changes(old_functions, new_functions)
