# conftest.py for app/ subdirectory
# Ensures pytest can discover tests from the project root's tests/ directory
# when run from this directory via the app/tests -> ../tests symlink.
import importlib
import os
import sys

# Add the project root to sys.path so test imports resolve
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Re-export symbols from the root conftest so that test files using
# `from conftest import PRODUCT_TYPES` resolve correctly when pytest
# runs from app/ (which finds this conftest first).
_root_conftest_path = os.path.join(_project_root, "tests", "conftest.py")
if os.path.exists(_root_conftest_path):
    _spec = importlib.util.spec_from_file_location("root_conftest", _root_conftest_path)
    _root_conftest = importlib.util.module_from_spec(_spec)
    try:
        _spec.loader.exec_module(_root_conftest)
        # Re-export the constants that test files import
        for _name in ("PRODUCT_TYPES", "MODEL_KEYS", "SCENARIOS"):
            if hasattr(_root_conftest, _name):
                globals()[_name] = getattr(_root_conftest, _name)
        # Re-export fixtures so pytest discovers them
        for _name in dir(_root_conftest):
            _obj = getattr(_root_conftest, _name)
            if callable(_obj) and hasattr(_obj, "pytestmark"):
                globals()[_name] = _obj
    except Exception:
        pass  # Non-fatal: tests that don't need these symbols still work
