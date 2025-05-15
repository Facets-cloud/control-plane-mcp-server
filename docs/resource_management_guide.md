# Control Plane Resource Management Guide for LLMs

## Overview

Control Plane manages infrastructure through projects (also called stacks or blueprints) that contain multiple resources. Each resource has a specific type that defines its purpose (e.g., service, ingress, postgres, redis). This guide explains how to interact with the Control Plane MCP server to manage these resources effectively.

## Key Concepts

- **Project/Stack/Blueprint**: A collection of related infrastructure resources (terms used interchangeably)
- **Resource/Intent**: Infrastructure components with specific types (service, postgres, redis, etc.)
- **Flavor**: Variations of a resource type with different characteristics
- **Version**: The implementation version of a resource type
- **Inputs**: Dependencies between resources (one resource referencing outputs from another)
- **Spec**: The configuration section that defines resource behavior
- **Environment/Cluster**: Deployment targets (dev, staging, production, etc.)
- **Resource Overrides**: Environment-specific configurations that modify base resource settings

## Working with Resources

### Discovering Available Resources

**Before creating any resource**, determine what's available:

1. **List Available Resource Types**: Use `list_available_resources(project_name)` to see all available resource types, their flavors, and versions
2. **Understand Resource Dependencies**: Use `get_module_inputs(project_name, resource_type, flavor)` to see what dependencies a resource requires
3. **Get Resource Schema**: Use `get_spec_for_module(project_name, resource_type, flavor, version)` to understand configuration options
4. **Get Sample Configuration**: Use `get_sample_for_module(project_name, resource_type, flavor, version)` for a complete template

### Creating New Resources

Follow this workflow when a user wants to add infrastructure:

```
User Request: "Add a PostgreSQL database to my project"

Your Process:
1. Call list_available_resources(project_name) → Find postgres type, note flavor/version
2. Call get_module_inputs(project_name, "postgres", flavor) → Check dependencies
3. Call get_spec_for_module(...) → Understand configuration schema
4. Call get_sample_for_module(...) → Get template
5. Customize the template based on user requirements
6. Call add_resource() with the final configuration
```

**Important**: If a resource requires inputs from other resources that don't exist, create those dependencies first. Always ask the user to choose when multiple options are available.

### Modifying Existing Resources

To update a resource's configuration:

1. **Get Current State**: `get_resource_by_project(project_name, resource_type, resource_name)`
2. **Check Schema**: `get_spec_for_resource(project_name, resource_type, resource_name)` 
3. **Modify Configuration**: Update the content while respecting the schema
4. **Apply Changes**: `update_resource(project_name, resource_type, resource_name, updated_content)`

### Viewing Resources

- **List All Resources**: `get_all_resources_by_project(project_name)`
- **Get Specific Resource**: `get_resource_by_project(project_name, resource_type, resource_name)`

## Environment Management and Overrides

### Understanding Environments

Projects can be deployed to multiple environments (dev, staging, production). Each environment can have customized configurations through overrides without changing the base project.

### Working with Environment Overrides

**Set Environment Context First**: Always use `env_tools.use_environment("environment-name")` before working with environment-specific resources.

#### Viewing Resources in Environments

- **List Environment Resources**: `get_all_resources_by_environment()`
- **Get Resource with Override Info**: `get_resource_by_environment(resource_type, resource_name)`

The environment resource view shows:
- `base_config`: Original configuration from the project
- `overrides`: Environment-specific modifications
- `effective_config`: Final merged configuration (base + overrides)
- `is_overridden`: Whether the resource has environment-specific changes

#### Managing Overrides

**Recommended Approach - Property-Level Changes**:

1. **Preview Changes**: `preview_override_effect(resource_type, resource_name, property_path, value)`
2. **Add/Update Property**: `add_or_update_override_property(resource_type, resource_name, property_path, value)`
3. **Remove Property**: `remove_override_property(resource_type, resource_name, property_path)`

**Complete Override Management**:

- **Replace All Overrides**: `replace_all_overrides(resource_type, resource_name, override_data)`
- **Clear All Overrides**: `clear_all_overrides(resource_type, resource_name)`

**Property Path Format**: Use dot notation for nested properties (e.g., `"spec.replicas"`, `"spec.resources.limits.memory"`)

#### Common Override Scenarios

**Scaling Differences**:
```
# Development environment
add_or_update_override_property("service", "web-app", "spec.replicas", 1)
add_or_update_override_property("service", "web-app", "spec.resources.limits.memory", "256Mi")

# Production environment
add_or_update_override_property("service", "web-app", "spec.replicas", 10)
add_or_update_override_property("service", "web-app", "spec.resources.limits.memory", "2Gi")
```

**Environment Variables**:
```
# Add debug settings for staging
add_or_update_override_property("service", "api", "spec.env", [
    {"name": "DEBUG", "value": "true"},
    {"name": "LOG_LEVEL", "value": "debug"}
])
```

**Database Sizing**:
```
# Smaller database for development
add_or_update_override_property("postgres", "main-db", "spec.storage.size", "5Gi")

# Larger database for production  
add_or_update_override_property("postgres", "main-db", "spec.storage.size", "100Gi")
```

### Override Validation

**Critical**: The effective configuration (base + overrides) must conform to the resource's schema. Always:

1. Check the schema: `get_spec_for_resource(resource_type, resource_name)`
2. Preview changes: `preview_override_effect()` before applying
3. Verify the effective configuration is valid

## Special Field Handling

### Secret References (x-ui-secret-ref annotation)

When a schema field has `x-ui-secret-ref`:
- **Never store sensitive values directly**
- Use the reference format: `"${blueprint.self.secrets.<secret_name>}"`
- Call `explain_ui_annotation("x-ui-secret-ref")` for detailed instructions

### Output References (x-ui-output-type annotation)

When a schema field has `x-ui-output-type`:
- Call `get_output_references(project_name, output_type)` to see available outputs
- Ask the user to select from available options
- Use the reference format provided by the tool
- Call `explain_ui_annotation("x-ui-output-type")` for detailed instructions

## Best Practices for LLM Interactions

### 1. Always Validate First
- Check current resource state before making changes
- Understand schema requirements before updates
- Use preview functions to validate overrides

### 2. Handle Dependencies Properly
- Ensure all required inputs exist before creating resources
- Check for dependent resources before deletion
- Ask users to choose when multiple options exist for inputs

### 3. Secure Data Handling
- Always use secret references for sensitive information
- Never include actual passwords, keys, or tokens in configurations

### 4. Clear Communication
- When multiple options exist (inputs, outputs), present them clearly to the user
- Explain the implications of changes, especially for overrides
- Provide context about what environments and overrides will affect

### 5. Structured Workflow
- Set environment context when working with overrides
- Follow the create → preview → apply → verify pattern
- Document any assumptions made during resource creation

## Error Handling

### Common Issues

1. **Schema Validation Errors**: Effective configuration doesn't match the required schema
   - Solution: Check schema requirements and adjust overrides accordingly

2. **Missing Dependencies**: Required inputs reference non-existent resources
   - Solution: Create dependencies first or update input references

3. **Invalid Override Property Paths**: Path doesn't exist in the resource structure
   - Solution: Verify property paths against the resource schema

4. **Environment Not Set**: Attempting override operations without setting environment
   - Solution: Always call `env_tools.use_environment()` first

### Recovery Strategies

- Use `get_resource_by_environment()` to inspect current state and errors
- Use `preview_override_effect()` to test changes before applying
- Use `clear_all_overrides()` as a last resort to return to base configuration
- Check schema documentation when validation fails

## Summary

This MCP server provides comprehensive tools for managing Control Plane infrastructure. The key to successful interaction is understanding the relationship between projects, resources, environments, and overrides. Always follow the validation → preview → apply → verify pattern, especially when working with environment overrides.