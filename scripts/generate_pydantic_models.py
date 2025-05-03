import os
from typing import Any

from swagger_client.models import Variables, AbstractCluster, FacetsResource, DeploymentRequest  # Add more as needed

from pydantic import BaseModel, Field

OUTPUT_DIR = "pydantic_generated"

TYPE_MAP = {
    'str': 'str',
    'bool': 'bool',
    'int': 'int',
    'float': 'float',
    'dict': 'dict',
    'list': 'list',
}

def to_safe_name(name: str) -> str:
    return name.lstrip("_") + "_" if name.startswith("_") else name

def generate_pydantic_class_code(class_name: str, swagger_cls: Any) -> str:
    lines = [f"class {class_name}(BaseModel):"]
    swagger_types = swagger_cls.swagger_types
    attr_map = swagger_cls.attribute_map

    for attr, type_str in swagger_types.items():
        py_type = TYPE_MAP.get(type_str, "Any")
        safe_attr = to_safe_name(attr)
        alias = attr_map.get(attr, attr)

        if safe_attr != alias:
            lines.append(f"    {safe_attr}: {py_type} = Field(None, alias='{alias}')")
        else:
            lines.append(f"    {safe_attr}: {py_type} = None")

    lines.append("\n    class Config:")
    lines.append("        validate_by_name = True")
    lines.append("        allow_population_by_alias = True")
    lines.append("        from_attributes = True")

    return "\n".join(lines)

def write_model_to_file(class_name: str, swagger_cls: Any):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{class_name.lower()}.py")

    code = (
        "# This file was auto-generated. Do not edit manually.\n"
        "from pydantic import BaseModel, Field\n"
        "from typing import Any, Optional\n\n" +
        generate_pydantic_class_code(class_name, swagger_cls)
    )

    with open(path, "w") as f:
        f.write(code)
    print(f"✅ Generated {path}")

if __name__ == "__main__":
    write_model_to_file("VariablesModel", Variables)
    write_model_to_file("AbstractClusterModel", AbstractCluster)
    write_model_to_file("FacetsResourceModel", FacetsResource)
    write_model_to_file("DeploymentRequestModel", DeploymentRequest)
    # Add more models here if needed
