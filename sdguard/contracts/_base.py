"""Base model shared by every contract: unknown fields are rejected and records are immutable."""

from pydantic import BaseModel, ConfigDict


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
