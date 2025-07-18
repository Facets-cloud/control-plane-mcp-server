from jsonschema import Draft7Validator
from jsonschema import validate
from typing import Dict, Any
from copy import deepcopy

# resource schema
resource_schema = {
    "$schema": "https://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "kind": {"type": "string"},
        "flavor": {"type": "string"},
        "version": {"type": "string"},
        # "spec": Draft7Validator.META_SCHEMA,  # Use the nested object schema
        "spec": {"type": "object"},
    },
    "required": ["kind", "flavor", "version", "spec"],
}

def validate_resource(resource_data: Dict[str, Any], resource_spec_schema: Dict[str, Any]):
    """
    Validates a resource's configuration data by comparing it against a defined resource schema.
    ONLY IF no specification schema for resource is available (i.e., get_spec_for_resource() returns No schema), simply pass an empty dictionary ({}).

    Args:
        resource_data: A dictionary representing the resource's configuration data. It should include key details like the resource's name, type, and its current configuartion under the "content" field.
        resource_spec_schema: The specification schema produced by get_spec_for_resource() to validate resource_data. Pass an empty dictionary ({}) ONLY IF no schema is available
        
    Returns:
        True if the validation is successful; otherwise, returns an error message indicating the validation failure.
    """
    # create a copy of resource schema
    resource_schema_copy = deepcopy(resource_schema)

    # Check if content is provided
    if not resource_data.get("content"):
        raise ValueError("content not provided in resource. content must be specified to create or update a resource. Please provide content in the resource.")

    # Update spec in resource_schema
    if resource_spec_schema:
        resource_schema_copy["properties"]["spec"] = resource_spec_schema

    try:
        # Validate the resource data content
        validate(instance=resource_data.get("content"), schema=resource_schema_copy)
    except Exception as e:
        raise type(e)(message = f"Validation failed for resource '{resource_data.get('name', 'Unknown')}' of type '{resource_data.get('type', 'Unknown')}'.\nException type: {type(e).__name__}\nDetails: {e}")
    
    return True