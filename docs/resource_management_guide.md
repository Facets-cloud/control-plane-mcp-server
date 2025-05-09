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

### Resource Overrides

Resource overrides allow you to customize resource configurations for specific environments without changing the base project configuration. This is particularly useful for:

1. **Environment-specific scaling**: Use different replica counts, memory limits, or CPU requirements in different environments.
2. **Configuration differences**: Set different environment variables, feature flags, or connection strings per environment.
3. **Security boundaries**: Apply stricter security settings in production while maintaining flexibility in development.

Overrides only modify the specified properties; all other properties are inherited from the base resource configuration in the project.

## Working with Environments and Overrides

### Viewing Environment Resources

To see what resources exist in an environment:

1. First set the current environment using `env_tools.use_environment("environment-name")`
2. Then use `get_all_resources_by_environment()` to list all resources in the environment
3. Use `get_resource_by_environment(resource_type, resource_name)` to view details of a specific resource

### Creating Resource Overrides

To create or update overrides for a resource in an environment:

1. Set the current environment using `env_tools.use_environment("environment-name")`
2. Get the current resource configuration to understand what can be overridden
3. Create an override object with only the properties you want to change
4. Use `override_resource(resource_type, resource_name, override_data)` to apply the override
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