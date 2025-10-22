from typing import Any

from ...foundations.carries_some_hooks_protocol import CarriesSomeHooksProtocol

from ..hooks.hook_aliases import Hook

from .nexus import Nexus


def collect_all_hook_nexuses(dict_of_carries_hooks: dict[str, CarriesSomeHooksProtocol[Any, Any]]) -> dict[Nexus[Any], list[tuple[str, CarriesSomeHooksProtocol[Any, Any], Hook[Any]]]]:

    hook_nexuses: dict[Nexus[Any], list[tuple[str, CarriesSomeHooksProtocol[Any, Any], Hook[Any]]]] = {}
    for name, carries_hook in dict_of_carries_hooks.items():
        for hook in carries_hook._get_dict_of_hooks().values(): # type: ignore
            hook_nexus = hook._get_nexus() # type: ignore
            if hook_nexus not in hook_nexuses:
                hook_nexuses[hook_nexus] = []
            hook_nexuses[hook_nexus].append((name, carries_hook, hook))
    return hook_nexuses

def write_report(dict_of_carries_hooks: dict[str, CarriesSomeHooksProtocol[Any, Any]]) -> str:
    """
    Generate a comprehensive report of nexuses and their usage across observables.
    
    Args:
        dict_of_carries_hooks: Dictionary mapping observable names to CarriesSomeHooksProtocol objects
        
    Returns:
        Formatted string report showing nexus usage and relationships
    """

    if not dict_of_carries_hooks:
        return "No observables provided.\n"

    nexuses = collect_all_hook_nexuses(dict_of_carries_hooks)
    
    if not nexuses:
        return "No nexuses found in the provided observables.\n"
    
    # Sort nexuses by number of connections (most connected first)
    sorted_nexuses = sorted(nexuses.items(), key=lambda x: len(x[1]), reverse=True)
    
    report = "=" * 80 + "\n"
    report += "📊 NEXUS ANALYSIS REPORT\n"
    report += "=" * 80 + "\n\n"
    
    # Summary statistics
    total_nexuses = len(nexuses)
    shared_nexuses = sum(1 for _, hooks_info in nexuses.items() if len(hooks_info) > 1)
    unshared_nexuses = total_nexuses - shared_nexuses
    total_hooks = sum(len(hooks_info) for _, hooks_info in nexuses.items())
    
    report += f"📈 SUMMARY:\n"
    report += f"   • Total Nexuses: {total_nexuses}\n"
    report += f"   • Shared Nexuses: {shared_nexuses}\n"
    report += f"   • Unshared Nexuses: {unshared_nexuses}\n"
    report += f"   • Total Hooks: {total_hooks}\n"
    report += f"   • Total Observables: {len(dict_of_carries_hooks)}\n\n"
    
    # Detailed nexus analysis
    report += "🔗 NEXUS DETAILS:\n"
    report += "-" * 80 + "\n\n"
    
    for i, (hook_nexus, owner_name_and_hooks) in enumerate(sorted_nexuses, 1):
        is_shared = len(owner_name_and_hooks) > 1
        nexus_type = "🔗 SHARED" if is_shared else "🔸 INDIVIDUAL"
        
        report += f"{i:2d}. {nexus_type} Nexus (ID: {hook_nexus.nexus_id})\n"
        report += f"    Value: {repr(hook_nexus.stored_value)}\n"
        report += f"    Connections: {len(owner_name_and_hooks)}\n"
        report += f"    Used by:\n"
        
        # Group by observable name for better organization
        observable_groups: dict[str, list[tuple[CarriesSomeHooksProtocol[Any, Any], Hook[Any]]]] = {}
        for owner_name, carries_hook, hook in owner_name_and_hooks:
            if owner_name not in observable_groups:
                observable_groups[owner_name] = []
            observable_groups[owner_name].append((carries_hook, hook))
        
        for owner_name, hook_pairs in sorted(observable_groups.items()):
            report += f"      📦 {owner_name}:\n"
            for carries_hook, hook in hook_pairs:
                hook_info = _get_hook_info(carries_hook, hook)
                report += f"         {hook_info}\n"
        
        report += "\n"
    
    # Connection analysis
    if shared_nexuses > 0:
        report += "🔍 CONNECTION ANALYSIS:\n"
        report += "-" * 80 + "\n"
        
        # Find most connected observables
        observable_connections: dict[str, int] = {}
        for hook_nexus, hooks_info in nexuses.items():
            if len(hooks_info) > 1:  # Only count shared connections
                for owner_name, carries_hook, hook in hooks_info:
                    observable_connections[owner_name] = observable_connections.get(owner_name, 0) + 1
        
        if observable_connections:
            report += "Most Connected Observables:\n"
            for name, count in sorted(observable_connections.items(), key=lambda x: x[1], reverse=True):
                report += f"   • {name}: {count} shared connections\n"
        
        report += "\n"
    
    report += "=" * 80 + "\n"
    return report


def _get_hook_info(carries_hook: CarriesSomeHooksProtocol[Any, Any], hook: Hook[Any]) -> str:
    """
    Get detailed information about a hook including its type and key.
    
    Args:
        carries_hook: The observable that carries this hook
        hook: The hook to analyze
        
    Returns:
        Formatted string with hook information
    """
    try:
        # Try to get the key for this hook
        hook_key = carries_hook._get_key_by_hook_or_nexus(hook)  # type: ignore
        hook_type = "primary"
    except ValueError:
        try:
            # Try secondary hooks if primary fails
            hook_key = carries_hook._get_key_by_hook_or_nexus(hook)  # type: ignore
            hook_type = "secondary"
        except ValueError:
            # Fallback if neither works
            hook_key = "unknown"
            hook_type = "unknown"
    
    # Check if this is a BaseXObject to get more specific info
    observable_type = "Unknown"
    if hasattr(carries_hook, '__class__'):
        observable_type = carries_hook.__class__.__name__
    
    # Format the hook information
    hook_info = f"key='{hook_key}' ({hook_type})"
    
    # Add additional info for BaseXObject instances
    if hasattr(carries_hook, '_primary_hooks') and hasattr(carries_hook, '_secondary_hooks'):
        if hook_type == "primary":
            hook_info += f" [Primary Hook]"
        elif hook_type == "secondary":
            hook_info += f" [Secondary Hook]"
    
    return f"└─ {hook_info} ({observable_type})"
