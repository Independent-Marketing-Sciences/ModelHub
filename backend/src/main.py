"""
FastAPI Backend for Modelling Mate
Main entry point - imports and registers all module routes
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import module routers
from modules.prophet import routes as prophet_routes
from modules.correlation import routes as correlation_routes
from modules.regression import routes as regression_routes
from modules.transformations import routes as transformation_routes
from modules.feature_extraction import routes as feature_extraction_routes
from modules.modelling import routes as modelling_routes

# Try to import Prophet to check availability
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

app = FastAPI(title="Modelling Mate Backend", version="1.0.0")

# CORS middleware to allow requests from Electron frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register module routers
app.include_router(prophet_routes.router, prefix="/api/prophet", tags=["Prophet"])
app.include_router(correlation_routes.router, prefix="/api/correlation", tags=["Correlation"])
app.include_router(regression_routes.router, prefix="/api/regression", tags=["Regression"])
app.include_router(transformation_routes.router, prefix="/api/transform", tags=["Transformations"])
app.include_router(feature_extraction_routes.router, prefix="/api/feature-extraction", tags=["Feature Extraction"])
app.include_router(modelling_routes.router, prefix="/api/modelling", tags=["Modelling"])


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "Modelling Mate Python Backend",
        "version": "1.0.0",
        "prophet_available": PROPHET_AVAILABLE
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "dependencies": {
            "prophet": PROPHET_AVAILABLE,
            "pandas": True,
            "numpy": True,
            "scipy": True,
            "sklearn": True
        }
    }


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    import socket
    import sys

    def find_free_port(start_port=8000, max_attempts=10):
        """Find a free port starting from start_port"""
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        raise RuntimeError(f"Could not find a free port between {start_port} and {start_port + max_attempts}")

    # Find a free port
    port = find_free_port()

    # Write port to a file so Electron can read it
    import os
    port_file = os.path.join(os.path.dirname(__file__), 'backend_port.txt')

    # Ensure directory exists and is writable
    try:
        os.makedirs(os.path.dirname(port_file), exist_ok=True)
        with open(port_file, 'w', encoding='utf-8') as f:
            f.write(str(port))
        print(f"Port file written to: {port_file}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"Warning: Could not write port file: {e}", file=sys.stderr, flush=True)

    print(f"Starting server on port {port}", file=sys.stderr, flush=True)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
