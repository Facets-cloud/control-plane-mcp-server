from typing import Dict, Any
import copy


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries. Override values take precedence over base values.
    
    Args:
        base: Base dictionary
        override: Override dictionary
        
    Returns:
        Dict[str, Any]: Merged dictionary
    """
    result = copy.deepcopy(base)
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = deep_merge(result[key], value)
        else:
            # Override the value (including lists and primitives)
            result[key] = copy.deepcopy(value)
    
    return result
