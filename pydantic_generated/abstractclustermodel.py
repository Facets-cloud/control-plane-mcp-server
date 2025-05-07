# This file was auto-generated. Do not edit manually.
from pydantic import BaseModel, Field
from typing import Any, Optional

class AbstractClusterModel(BaseModel):
    auto_sign_off_schedule: str = Field(None, alias='autoSignOffSchedule')
    base_cluster_id: str = Field(None, alias='baseClusterId')
    base_cluster_name: str = Field(None, alias='baseClusterName')
    branch: str = None
    cd_pipeline_parent: str = Field(None, alias='cdPipelineParent')
    cloud: str = None
    cloud_account_id: str = Field(None, alias='cloudAccountId')
    cloud_account_secret_id: str = Field(None, alias='cloudAccountSecretId')
    cluster_code: str = Field(None, alias='clusterCode')
    cluster_state: str = Field(None, alias='clusterState')
    common_environment_variables: Any = Field(None, alias='commonEnvironmentVariables')
    component_versions: Any = Field(None, alias='componentVersions')
    configured: bool = None
    created_by: str = Field(None, alias='createdBy')
    creation_date: Any = Field(None, alias='creationDate')
    deleted: bool = None
    dynamic_launch: bool = Field(None, alias='dynamicLaunch')
    enable_auto_sign_off: bool = Field(None, alias='enableAutoSignOff')
    entity_type: str = Field(None, alias='entityType')
    global_variables: Any = Field(None, alias='globalVariables')
    id: str = None
    is_ephemeral: bool = Field(None, alias='isEphemeral')
    k8s_requests_to_limits_ratio: float = Field(None, alias='k8sRequestsToLimitsRatio')
    last_modified_by: str = Field(None, alias='lastModifiedBy')
    last_modified_date: Any = Field(None, alias='lastModifiedDate')
    name: str = None
    namespace: str = None
    number_of_versions: int = Field(None, alias='numberOfVersions')
    pause_releases: bool = Field(None, alias='pauseReleases')
    release_stream: str = Field(None, alias='releaseStream')
    require_sign_off: bool = Field(None, alias='requireSignOff')
    schedules: Any = None
    secrets: Any = None
    secrets_uid: str = Field(None, alias='secretsUid')
    stack_name: str = Field(None, alias='stackName')
    tz: str = None
    variables: Any = None
    versioning_key: str = Field(None, alias='versioningKey')

    class Config:
        validate_by_name = True
        allow_population_by_alias = True
        from_attributes = True