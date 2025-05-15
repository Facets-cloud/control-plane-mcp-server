from typing import Dict, Any, Optional


def get_nested_property(obj: Dict[str, Any], property_path: str) -> Any:
    """
    Get a nested property from an object using dot notation.
    
    Args:
        obj: The object to traverse
        property_path: Dot-separated path (e.g., "spec.replicas")
        
    Returns:
        The value at the specified path, or None if not found
    """
    if not property_path:
        return obj
    
    current = obj
    for part in property_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def set_nested_property(obj: Dict[str, Any], property_path: str, value: Any) -> None:
    """
    Set a nested property in an object using dot notation.
    Creates intermediate objects as needed.
    
    Args:
        obj: The object to modify
        property_path: Dot-separated path (e.g., "spec.replicas")
        value: The value to set
    """
    if not property_path:
        return
    
    parts = property_path.split(".")
    current = obj
    
    # Navigate to the parent of the target property
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    
    # Set the final property
    current[parts[-1]] = value


def remove_nested_property(obj: Dict[str, Any], property_path: str) -> bool:
    """
    Remove a nested property from an object using dot notation.
    Cleans up empty parent objects.
    
    Args:
        obj: The object to modify
        property_path: Dot-separated path (e.g., "spec.replicas")
        
    Returns:
        True if the property was found and removed, False otherwise
    """
    if not property_path:
        return False
    
    parts = property_path.split(".")
    current = obj
    parents = []
    
    # Navigate to the parent of the target property, keeping track of parents
    for i, part in enumerate(parts[:-1]):
        if not isinstance(current, dict) or part not in current:
            return False
        parents.append((current, part))
        current = current[part]
    
    # Remove the final property
    final_key = parts[-1]
    if not isinstance(current, dict) or final_key not in current:
        return False
    
    del current[final_key]
    
    # Clean up empty parent objects
    for parent_obj, key in reversed(parents):
        if not parent_obj[key]:  # If the child object is now empty
            del parent_obj[key]
        else:
            break  # Stop if we find a non-empty parent
    
    return True
