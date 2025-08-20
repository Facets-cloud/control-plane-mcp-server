from jsonschema import Draft7Validator
from jsonschema import validate, ValidationError
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


def validate_resource_with_public_schema(content: Dict[str, Any], schema_response: Dict[str, Any]) -> bool:
    """
    Validates a resource's configuration content against the organization's complete schema
    from the public API (get_resource_schema_public).
    
    This provides strict JSON schema validation using the actual organization-defined schema
    with all properties, types, constraints, and special annotations.
    
    Args:
        content: The resource configuration content to validate
        schema_response: Complete schema response from get_resource_schema_public()
        
    Returns:
        True if validation is successful
        
    Raises:
        ValueError: If validation fails with detailed error information
    """
    if not content:
        raise ValueError("Content cannot be empty. Resource configuration content must be provided.")
    
    if not schema_response or not schema_response.get("properties"):
        raise ValueError("Invalid schema response. Schema must contain properties definition.")
    
    # Build complete JSON schema from the public API response
    json_schema = {
        "$schema": "https://json-schema.org/draft-07/schema#",
        "type": schema_response.get("type", "object"),
        "properties": schema_response.get("properties", {}),
        "required": schema_response.get("required", []),
        "additionalProperties": schema_response.get("additional_properties", True)
    }
    
    try:
        # Perform strict JSON schema validation
        validate(instance=content, schema=json_schema)
        return True
        
    except ValidationError as e:
        # Create detailed error message with path and schema context
        error_path = " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
        
        # Extract property information if available
        property_info = ""
        if e.absolute_path and len(e.absolute_path) > 0:
            prop_name = e.absolute_path[-1]
            if prop_name in json_schema.get("properties", {}):
                prop_schema = json_schema["properties"][prop_name]
                property_info = f"\nExpected type: {prop_schema.get('type', 'unknown')}"
                if "enum" in prop_schema:
                    property_info += f"\nValid values: {prop_schema['enum']}"
                if "description" in prop_schema:
                    property_info += f"\nDescription: {prop_schema['description']}"
        
        error_message = (
            f"Schema validation failed at '{error_path}': {e.message}"
            f"{property_info}"
            f"\nSchema validation ensures your resource configuration matches the organization's defined structure."
        )
        
        raise ValueError(error_message)
        
    except Exception as e:
        raise ValueError(f"Schema validation error: {str(e)}")


def get_schema_validation_summary(schema_response: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of the schema requirements for documentation/debugging.
    
    Args:
        schema_response: Complete schema response from get_resource_schema_public()
        
    Returns:
        String summary of schema requirements
    """
    if not schema_response:
        return "No schema information available"
    
    summary = []
    summary.append(f"Schema Type: {schema_response.get('type', 'unknown')}")
    
    required_fields = schema_response.get("required", [])
    if required_fields:
        summary.append(f"Required Fields: {', '.join(required_fields)}")
    
    properties = schema_response.get("properties", {})
    if properties:
        summary.append(f"Available Properties: {len(properties)} fields")
        
        # Show a few sample properties with types
        sample_props = list(properties.items())[:5]
        for prop_name, prop_def in sample_props:
            prop_type = prop_def.get("type", "unknown") 
            is_required = prop_name in required_fields
            req_marker = " (required)" if is_required else ""
            summary.append(f"  - {prop_name}: {prop_type}{req_marker}")
        
        if len(properties) > 5:
            summary.append(f"  ... and {len(properties) - 5} more properties")
    
    additional_props = schema_response.get("additional_properties", True)
    summary.append(f"Custom Properties Allowed: {additional_props}")
    
    return "\n".join(summary)