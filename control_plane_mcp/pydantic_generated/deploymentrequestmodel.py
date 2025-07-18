# This file was auto-generated. Do not edit manually.
from pydantic import BaseModel, Field
from typing import Any, Optional, List


class TfVersion(BaseModel):
    majorVersion: str
    minorVersion: str
    tfStream: str

    class Config:
        from_attributes = True
        allow_population_by_alias = True
        from_attributes = True

class DeploymentRequestModel(BaseModel):
    allow_destroy: bool = Field(None, alias='allowDestroy')
    alpha: bool = None
    approved_release: bool = Field(None, alias='approvedRelease')
    can_queue: bool = Field(None, alias='canQueue')
    extra_env: Any = Field(None, alias='extraEnv')
    force_release: bool = Field(None, alias='forceRelease')
    hotfix_resources: Any = Field(None, alias='hotfixResources')
    lock_id: str = Field(None, alias='lockId')
    override_build_steps: List[str] = Field(None, alias='overrideBuildSteps')
    parallel_release: bool = Field(None, alias='parallelRelease')
    plan_code_build_id: str = Field(None, alias='planCodeBuildId')
    queued_release_id: str = Field(None, alias='queuedReleaseId')
    release_comment: str = Field(None, alias='releaseComment')
    release_trace_id: str = Field(None, alias='releaseTraceId')
    release_type: str = Field(None, alias='releaseType')
    tf_version: TfVersion = Field(None, alias='tfVersion')
    with_refresh: bool = Field(None, alias='withRefresh')

    class Config:
        validate_by_name = True
        allow_population_by_alias = True
        from_attributes = True

