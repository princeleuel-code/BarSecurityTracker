from fastapi.testclient import TestClient
import sys
import os

# Add the 'src' directory to the Python path to allow imports like 'from api.main import app'
# This assumes 'tests' is directly under 'thermal-ai-kit' and 'src' is also under 'thermal-ai-kit'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Now try to import the app from the api.main module
# If 'app' is not directly importable, this might need adjustment
# depending on how FastAPI app instance is exposed in api/main.py
try:
    from api.main import app # Assuming 'app' is the FastAPI instance in api/main.py
except ImportError as e:
    # Fallback if src is not in path correctly or app is not exposed
    # This is a common issue in testing setups.
    # For a robust solution, consider structuring as a package or using PYTHONPATH.
    print(f"Error importing FastAPI app: {e}. Ensure PYTHONPATH is set or structure allows direct import.")
    # As a simple fallback for this specific test, if 'app' cannot be imported,
    # we can't run the test. Pytest will show an error.
    # A more complex setup might involve creating the app instance within the test.
    # For now, we rely on the sys.path modification and 'app' being importable.
    raise # Re-raise the import error so it's visible

client = TestClient(app)

def test_health_check():
    """
    Tests the /healthz endpoint.
    """
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_read_root():
    """
    Tests the root / endpoint.
    """
    response = client.get("/")
    assert response.status_code == 200
    # Assuming the root endpoint returns something like:
    # {"message": "Thermal AI Kit API is running. See /docs for API documentation."}
    # Adjust assertion based on actual root endpoint response in api/main.py
    assert "Thermal AI Kit API is running" in response.json().get("message", "")

# To run this test:
# 1. Ensure you are in the 'thermal-ai-kit' directory.
# 2. Run 'python -m pytest' or 'pytest'.
# Ensure that PYTHONPATH includes the 'src' directory if direct imports fail,
# e.g., export PYTHONPATH=$PYTHONPATH:$(pwd)/src (from thermal-ai-kit root)
