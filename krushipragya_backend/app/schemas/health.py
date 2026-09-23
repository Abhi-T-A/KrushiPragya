from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for basic application health check response."""
    status: str = Field(default="healthy", description="Application operational status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")


class DatabaseHealthResponse(BaseModel):
    """Schema for database connectivity health check response."""
    status: str = Field(..., description="Database check status: healthy or unhealthy")
    database: str = Field(..., description="Database connection state: connected or disconnected")
