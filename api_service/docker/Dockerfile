# ---- Builder Stage ----
# This stage builds the Python wheel package
FROM python:3.11-slim AS builder

# Set environment variables for the build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN pip install --upgrade pip build

# Copy only the files necessary to build the wheel
# Assumes the build context is the 'api_service' directory
COPY pyproject.toml README.md ./
COPY app/ ./app/

# Build the wheel
# The output will be in the 'dist' directory
RUN python -m build --wheel --outdir dist .


# ---- Final Runtime Stage ----
# This stage creates the final, lean production image
FROM python:3.11-slim AS runtime

# Set environment variables for runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # The app will be installed in site-packages, so we need to adjust the python path
    # if our main module is not directly importable.
    # Assuming your pyproject.toml defines the package correctly, this is often not needed.
    APP_MODULE="app.main:app"

WORKDIR /app

# Copy the built wheel from the builder stage
COPY --from=builder /app/dist/*.whl .

# Install the application wheel.
# This also installs all production dependencies listed in pyproject.toml.
# Using a virtual environment is not strictly necessary in a container
# as the container itself provides isolation.
RUN pip install --no-cache-dir *.whl

# Create a non-root user for security
RUN useradd --create-home appuser
USER appuser

# Health check (optional but recommended)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health') or exit(1)"

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]