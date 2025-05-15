# Control Plane Resource Management Guide

## Resource Management Overview

In Control Plane, a project (also called stack or blueprint) contains multiple resources that
are defined in JSON files. Each resource has a specific type (also called intent) such as
service, ingress, postgres, redis, etc. Resources can be interdependent, with some resources
requiring inputs from others.

## Key Concepts

- **Project/Stack/Blueprint**: These terms are used interchangeably to refer to a collection of resources.
- **Resource/Intent**: Each resource has a type/intent (e.g., service, ingress, postgres) that defines its purpose.
- **Flavor**: A variation of a resource type with specific characteristics.
- **Version**: The version of the resource type implementation.
- **Inputs**: References to other resources that this resource depends on.
- **Spec**: The configuration section of a resource that defines its behavior.
- **Environment/Cluster**: A deployment target for a project. Each project can have multiple environments (dev, staging, production, etc.).
- **Resource Overrides**: Environment-specific configurations that modify resource properties for a specific environment.

## Environment and Resource Override Concepts

### Environments

Environments (also called clusters) are separate instances where your project resources are deployed. A single project can be deployed to multiple environments, such as:

- Development (dev)
- Testing (test)
- Staging
- Production (prod)

Each environment has its own configuration, which allows you to customize how your resources behave in different contexts. For example, you might want:

- Fewer replicas of a service in development than in production
- Different memory and CPU limits across environments
- Environment-specific configuration parameters

### Resource Overrides and Schema Validation

Resource overrides allow you to customize resource configurations for specific environments without changing the base project configuration. This is particularly useful for:

1. **Environment-specific scaling**: Use different replica counts, memory limits, or CPU requirements in different environments.
2. **Configuration differences**: Set different environment variables, feature flags, or connection strings per environment.
3. **Security boundaries**: Apply stricter security settings in production while maintaining flexibility in development.

**IMPORTANT**: Overrides only modify the specified properties; all other properties are inherited from the base resource configuration in the project. **The effective configuration (base + overrides) must still conform to the original module's spec schema**.

#### Schema Validation Rules

When applying overrides, it's crucial to understand that:

1. **Base Configuration**: Must follow the module's spec schema (validated when created/updated in the project)
2. **Override Values**: Can override any property from the base configuration
3. **Effective Configuration**: The merged result (base + overrides) is validated against the module's spec schema

This means your overrides must produce a valid configuration according to the resource's module specification. For example:

```python
# Base config (in project):
{
  "spec": {
    "replicas": 3,
    "resources": {
      "limits": {"memory": "1Gi", "cpu": "500m"}
    }
  }
}

# Valid override (increases replicas):
{
  "spec": {
    "replicas": 10
  }
}

# Invalid override (wrong type for replicas):
{
  "spec": {
    "replicas": "ten"  # String instead of number - violates schema
  }
}
```

To ensure your overrides are valid:
- Use `get_spec_for_resource(resource_type, resource_name)` to check the schema requirements
- Use `preview_override_effect()` to see the effective configuration before applying overrides
- The schema from `get_spec_for_module()` or `get_spec_for_resource()` defines what's valid in the `spec` section

## Working with Environments and Overrides

### Viewing Environment Resources with Override Information

To see what resources exist in an environment and understand their override status:

1. **List All Resources**: First set the current environment using `env_tools.use_environment("environment-name")`
2. **List Resources**: Use `get_all_resources_by_environment()` to list all resources in the environment
3. **View Resource Details**: Use `get_resource_by_environment(resource_type, resource_name)` to get comprehensive details

The `get_resource_by_environment` function returns:
- `base_config`: The original configuration from the project
- `overrides`: Any environment-specific overrides applied
- `effective_config`: The final merged configuration (base + overrides)
- `is_overridden`: Boolean indicating if the resource has overrides
- Additional metadata like errors, directory, filename, etc.

Example:
## Environment Override Examples

### Complete Override Management Example

Here's a comprehensive example of working with environment overrides:

```python
# 1. Set the environment
env_tools.use_environment("production")

# 2. View current resource state
resource = get_resource_by_environment("service", "web-api")
print(f"Current replicas: {resource['effective_config']['spec']['replicas']}")
print(f"Has overrides: {resource['is_overridden']}")

# 3. Preview what would happen if we increase replicas
preview = preview_override_effect("service", "web-api", "spec.replicas", 10)
print(f"New effective replicas: {preview['proposed_effective_config']['spec']['replicas']}")

# 4. Apply the change
add_or_update_override_property("service", "web-api", "spec.replicas", 10)

# 5. Add memory limit override
add_or_update_override_property("service", "web-api", "spec.resources.limits.memory", "2Gi")

# 6. Add CPU limit override
add_or_update_override_property("service", "web-api", "spec.resources.limits.cpu", "1000m")

# 7. View the current overrides
final_resource = get_resource_by_environment("service", "web-api")
print(f"All overrides: {final_resource['overrides']}")
print(f"Final effective config: {final_resource['effective_config']}")

# 8. Remove CPU limit if we don't need it
remove_override_property("service", "web-api", "spec.resources.limits.cpu")

# 9. Set a complex override all at once (alternative approach)
complex_override = {
    "spec": {
        "replicas": 5,
        "resources": {
            "limits": {"memory": "1Gi"},
            "requests": {"memory": "512Mi"}
        },
        "env": [
            {"name": "ENVIRONMENT", "value": "production"},
            {"name": "LOG_LEVEL", "value": "warn"}
        ]
    }
}
replace_all_overrides("service", "web-api", complex_override)

# 10. Clear all overrides to revert to base configuration
clear_all_overrides("service", "web-api")
```

#### Complete Schema Validation Example

```python
# 1. Check the current resource and its schema
env_tools.use_environment("production")
resource = get_resource_by_environment("service", "web-app")
schema = get_spec_for_resource("service", "web-app")

# 2. Current base config (from project)
print("Base config:", resource['base_config']['spec'])
# Output: {"replicas": 3, "resources": {"limits": {"memory": "1Gi"}}}

# 3. Check schema to understand valid values for replicas
print("Replicas schema:", schema['properties']['spec']['properties']['replicas'])
# Output: {"type": "number", "minimum": 1}

# 4. Preview a valid override
preview = preview_override_effect("service", "web-app", "spec.replicas", 10)
print("Effective config with override:", preview['proposed_effective_config']['spec'])
# Output: {"replicas": 10, "resources": {"limits": {"memory": "1Gi"}}}

# 5. Apply the valid override
add_or_update_override_property("service", "web-app", "spec.replicas", 10)

# 6. Try an invalid override (wrong type)
try:
    preview_invalid = preview_override_effect("service", "web-app", "spec.replicas", "ten")
    # This would show effective config but might cause validation errors
except Exception as e:
    print(f"Invalid override might cause: {e}")
    # The system would reject this during validation
```

#### Scaling Overrides
```python
# Development: Lower resources
env_tools.use_environment("dev")
add_or_update_override_property("service", "app", "spec.replicas", 1)
add_or_update_override_property("service", "app", "spec.resources.limits.memory", "256Mi")

# Production: Higher resources
env_tools.use_environment("prod")
add_or_update_override_property("service", "app", "spec.replicas", 10)
add_or_update_override_property("service", "app", "spec.resources.limits.memory", "2Gi")
```

#### Environment Variables
```python
# Staging environment with debug enabled
env_tools.use_environment("staging")
add_or_update_override_property("service", "api", "spec.env", [
    {"name": "DEBUG", "value": "true"},
    {"name": "LOG_LEVEL", "value": "debug"}
])
```

#### Database Configuration
```python
# Different database sizes per environment
env_tools.use_environment("dev")
add_or_update_override_property("postgres", "main-db", "spec.storage.size", "5Gi")

env_tools.use_environment("prod")
add_or_update_override_property("postgres", "main-db", "spec.storage.size", "100Gi")
add_or_update_override_property("postgres", "main-db", "spec.resources.limits.memory", "8Gi")
```python
# Set environment
env_tools.use_environment("staging")

# Get resource with override information
resource_info = get_resource_by_environment("service", "web-app")
print(f"Base config: {resource_info['base_config']}")
print(f"Overrides: {resource_info['overrides']}")
print(f"Effective config: {resource_info['effective_config']}")
print(f"Is overridden: {resource_info['is_overridden']}")
```

### Creating Resource Overrides

To create or update overrides for a resource in an environment, you have several tools available:

#### Safe Property-Level Override Management

1. **Add or Update a Specific Property**:
   ```python
   add_or_update_override_property(resource_type, resource_name, property_path, value)
   ```
   - Safely adds or updates a single property using dot notation
   - Preserves all existing overrides
   - Example: `add_or_update_override_property("service", "web-app", "spec.replicas", 5)`
   - Example: `add_or_update_override_property("service", "web-app", "spec.resources.limits.memory", "1Gi")`

2. **Remove a Specific Property**:
   ```python
   remove_override_property(resource_type, resource_name, property_path)
   ```
   - Removes only the specified property
   - Automatically cleans up empty parent objects
   - Example: `remove_override_property("service", "web-app", "spec.replicas")`

3. **Preview Override Effects**:
   ```python
   preview_override_effect(resource_type, resource_name, property_path, value)
   ```
   - Shows what the effective configuration would be with a proposed change
   - Doesn't modify anything - just previews the result
   - Example: `preview_override_effect("service", "web-app", "spec.replicas", 5)`

#### Complete Override Management

4. **Replace All Overrides** (use with caution):
   ```python
   replace_all_overrides(resource_type, resource_name, override_data)
   ```
   - **WARNING**: Completely replaces all existing overrides
   - Use only when you want to start fresh or set complex overrides
   - Example: `replace_all_overrides("service", "web-app", {"spec": {"replicas": 3}})`

5. **Clear All Overrides**:
   ```python
   clear_all_overrides(resource_type, resource_name)
   ```
   - Removes all overrides for a resource
   - Resource will use only the base configuration
   - Example: `clear_all_overrides("service", "web-app")`

#### Recommended Workflow for Safe Override Management

1. **Set Environment**: `env_tools.use_environment("environment-name")`
2. **View Current State**: `get_resource_by_environment(resource_type, resource_name)`
3. **Check Schema**: `get_spec_for_resource(resource_type, resource_name)` to understand valid spec properties
4. **Preview Changes**: `preview_override_effect(resource_type, resource_name, property_path, value)`
5. **Apply Changes**: `add_or_update_override_property(resource_type, resource_name, property_path, value)`
6. **Verify Result**: Check the `effective_config` in the updated resource

**Pro Tip**: Always use the preview function to ensure your overrides produce a valid effective configuration before applying them.

### Handling Override Validation Errors

If you create an override that results in an invalid effective configuration, you might see validation errors when viewing the resource. These errors indicate that the merged configuration doesn't conform to the module's spec.

Common scenarios:
- Type mismatches (e.g., providing a string where a number is expected)
- Missing required fields after override
- Values outside allowed ranges or enums
- Invalid nested object structures

To fix validation errors:
1. Check the module's spec: `get_spec_for_resource(resource_type, resource_name)`
2. Review your overrides: `get_resource_by_environment(resource_type, resource_name)`
3. Adjust the override to match the schema requirements
4. Use the preview function to verify before applying changes
```
## Complete Resource Management Workflow

### 1. Viewing Existing Resources

To see what resources already exist in a project:
- Use `get_all_resources_by_project(project_name)` to list all resources in a project.
- Use `get_resource_by_project(project_name, resource_type, resource_name)` to view details of a specific resource.

### 2. Adding a New Resource

Follow this exact workflow when adding a new resource:

1. **Find Available Resource Types**:
   - Call `list_available_resources(project_name)` to see what resource types, flavors, and versions are available.
   - Select the desired resource_type/intent (e.g., 'service', 'postgres') and note its flavor and version.

2. **Check Required Inputs**:
   - Call `get_module_inputs(project_name, resource_type, flavor)` to see what inputs this resource requires.
   - For each non-optional input with multiple compatible resources, ASK THE USER which one to use.
   - Present options clearly: "For the 'database' input, available options are: X, Y, Z. Which would you like to use?"
   - If a required input has no compatible resources, you must create those dependencies first.

3. **Understand the Resource Schema**:
   - Call `get_spec_for_module(project_name, resource_type, flavor, version)` to get the schema that defines valid configuration options.
   - Call `get_sample_for_module(project_name, resource_type, flavor, version)` to get a complete template with sample values.

4. **Create and Customize Content**:
   - Start with the sample template from the previous step.
   - Modify it according to user requirements and the schema specifications.
   - Pay special attention to fields with annotations (see Special Annotations section).

5. **Add the Resource**:
   - Call `add_resource()` with all required parameters:
     - project_name, resource_type, resource_name, flavor, version
     - The customized content from step 4
     - A map of inputs where each key is an input name and each value is a dict with:
       * resource_name: The name of the selected resource
       * resource_type: The type of the selected resource
       * output_name: The output name from the selected resource

Example inputs parameter format:
```python
{
    "database": {
        "resource_name": "my-postgres",
        "resource_type": "postgres",
        "output_name": "postgres_connection"
    }
}
```

### 3. Updating an Existing Resource

Follow these steps when updating a resource:

1. **Get Current Configuration**:
   - Call `get_resource_by_project(project_name, resource_type, resource_name)` to retrieve the current configuration.
   - The "content" field contains the resource's current configuration.

2. **Understand the Schema**:
   - Call `get_spec_for_resource(project_name, resource_type, resource_name)` to understand the valid fields and values.
   - This shows the schema for the "spec" section of the resource JSON.

3. **Make Modifications**:
   - Create a modified version of the content based on the user's requirements.
   - Ensure changes conform to the schema obtained in step 2.
   - Be careful not to remove or alter required fields.

4. **Update the Resource**:
   - Call `update_resource(project_name, resource_type, resource_name, updated_content)` with the modified content.

### 4. Deleting a Resource

To delete a resource:
- Before deletion, check if other resources depend on it using `get_all_resources_by_project(project_name)`.
- Warn the user if dependencies exist, as deletion could break those resources.
- Call `delete_resource(project_name, resource_type, resource_name)` to remove the resource.

## Special Annotations

When reviewing resource schemas, watch for fields with special annotations:

### 1. Secret References (x-ui-secret-ref)

When a field has the `x-ui-secret-ref` annotation:
- Do NOT insert sensitive values directly in the JSON.
- Use the reference format: `"${blueprint.self.secrets.<name_of_secret>}"`.
- Ask if a secret has already been created, or if they want to create a new one.

Call `explain_ui_annotation("x-ui-secret-ref")` for detailed handling instructions.

### 2. Output References (x-ui-output-type)

When a field has the `x-ui-output-type` annotation:
- Call `get_output_references(project_name, output_type)` to find available outputs.
- Ask the user to choose from the list of available references.
- Use the reference format provided by the tool in the field.

Call `explain_ui_annotation("x-ui-output-type")` for detailed handling instructions.

## Best Practices

1. **Validate Before Updating**:
   - Always check the current resource state before making changes.
   - Understand the schema requirements before updating a resource.

2. **Handle Dependencies Carefully**:
   - When adding resources, ensure all required inputs are properly configured.
   - When deleting resources, check for dependencies that might be affected.

3. **Ask User for Resource Selection**:
   - When multiple options exist for inputs, always ask the user to choose.
   - Never select inputs automatically unless there's only one option or it's clearly specified.

4. **Secure Handling of Sensitive Data**:
   - Always use secret references for sensitive information.
   - Never include actual sensitive values in the resource JSON.