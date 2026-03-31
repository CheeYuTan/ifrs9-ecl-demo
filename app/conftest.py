# conftest.py for app/ subdirectory
# Ensures pytest can discover tests from the project root's tests/ directory
# when run from this directory.
import sys
import os

# Add the project root to sys.path so test imports resolve
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
