"""
Build State API Service
A FastAPI service for managing multi-cloud IaaS image build states.

This is the main application file following FastAPI best practices.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import init_database
from .routers import (
    health,
    auth,
    users,
    builds,
    dashboard,
    projects,
    state_codes,
    platforms,
    os_versions,
    image_types,
    artifacts,
    variables,
    resume,
)



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting Build State API...")
    try:
        init_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")

    yield

    # Shutdown
    print("Shutting down Build State API...")


# Create FastAPI application
app = FastAPI(
    title="Build State API",
    description="REST API for managing multi-cloud IaaS image build states",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
print("Including routers...")
app.include_router(health.router, tags=["Health"])
print("Health router included")
app.include_router(auth.router, tags=["Authentication"])
print("Auth router included")
app.include_router(users.router, tags=["Users"])
print("Users router included")
app.include_router(projects.router, tags=["Projects"])
print("Projects router included")
app.include_router(state_codes.router, tags=["State Codes"])
print("State Codes router included")
app.include_router(platforms.router, tags=["Platforms"])
print("Platforms router included")
app.include_router(os_versions.router, tags=["OS Versions"])
print("OS Versions router included")
app.include_router(image_types.router, tags=["Image Types"])
print("Image Types router included")
app.include_router(builds.router, tags=["Builds"])
print("Builds router included")
app.include_router(dashboard.router, tags=["Dashboard"])
print("Dashboard router included")
app.include_router(artifacts.router, tags=["Artifacts"])
print("Artifacts router included")
app.include_router(variables.router, tags=["Variables"])
print("Variables router included")
app.include_router(resume.router, tags=["Resume"])
print("Resume router included")
print("All routers included successfully")


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {"message": "Build State API", "version": "1.0.0", "instance": "api01"}


def main():
    """Main entry point for the application."""
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )


if __name__ == "__main__":
    main()