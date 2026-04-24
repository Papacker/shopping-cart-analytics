import sys
from unittest.mock import MagicMock

def test_app_imports():
    # Mockataan streamlit, jotta testi ei yritä avata selainta
    sys.modules['streamlit'] = MagicMock()
    try:
        import app
        assert True
    except ImportError:
        pytest.fail("App.py import epäonnistui")