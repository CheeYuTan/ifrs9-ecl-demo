"""Dedicated tests for ecl/config.py — configuration loading helpers."""
from unittest.mock import MagicMock, patch

import pytest

from ecl.config import _build_product_maps, _load_config, _schema, _prefix, _t
from ecl.constants import DEFAULT_LGD, DEFAULT_SAT, _FALLBACK_BASE_LGD, _FALLBACK_SATELLITE


class TestTableHelper:
    def test_t_combines_schema_and_prefix(self):
        with patch("ecl.config._schema", return_value="public"), \
             patch("ecl.config._prefix", return_value="ecl_"):
            result = _t("model_ready_loans")
            assert result == "public.ecl_model_ready_loans"

    def test_t_empty_prefix(self):
        with patch("ecl.config._schema", return_value="sch"), \
             patch("ecl.config._prefix", return_value=""):
            result = _t("table_name")
            assert result == "sch.table_name"


class TestBuildProductMaps:
    @patch("ecl.config.backend")
    def test_returns_two_dicts(self, mock_backend):
        mock_backend.query_df.side_effect = Exception("no db")
        with patch("ecl.config.admin_config", create=True) as mock_admin:
            mock_admin.get_config.side_effect = Exception("no config")
            base_lgd, sat_coeffs = _build_product_maps()
        assert isinstance(base_lgd, dict)
        assert isinstance(sat_coeffs, dict)

    @patch("ecl.config.backend")
    def test_fallback_lgd_used_when_no_config(self, mock_backend):
        mock_backend.query_df.side_effect = Exception("no db")
        with patch("ecl.config.admin_config", create=True) as mock_admin:
            mock_admin.get_config.side_effect = Exception("no config")
            base_lgd, _ = _build_product_maps()
        for product, lgd in _FALLBACK_BASE_LGD.items():
            assert base_lgd[product] == lgd

    @patch("ecl.config.backend")
    def test_fallback_satellite_used_when_no_config(self, mock_backend):
        mock_backend.query_df.side_effect = Exception("no db")
        with patch("ecl.config.admin_config", create=True) as mock_admin:
            mock_admin.get_config.side_effect = Exception("no config")
            _, sat_coeffs = _build_product_maps()
        for product in _FALLBACK_SATELLITE:
            assert product in sat_coeffs
            assert sat_coeffs[product]["pd_lgd_corr"] == _FALLBACK_SATELLITE[product]["pd_lgd_corr"]

    @patch("ecl.config.backend")
    def test_admin_lgd_overrides_fallback(self, mock_backend):
        mock_backend.query_df.side_effect = Exception("no db")
        import sys
        mock_admin = MagicMock()
        mock_admin.get_config.return_value = {
            "model": {"lgd_assumptions": {"credit_card": {"lgd": 0.70}}}
        }
        with patch.dict(sys.modules, {"admin_config": mock_admin}):
            base_lgd, _ = _build_product_maps()
        assert base_lgd["credit_card"] == 0.70

    @patch("ecl.config.backend")
    def test_new_product_from_db_gets_default_lgd(self, mock_backend):
        import pandas as pd
        mock_backend.query_df.return_value = pd.DataFrame({"product_type": ["exotic_bond"]})
        import sys
        mock_admin = MagicMock()
        mock_admin.get_config.side_effect = Exception("no config")
        with patch.dict(sys.modules, {"admin_config": mock_admin}):
            base_lgd, sat_coeffs = _build_product_maps()
        assert base_lgd["exotic_bond"] == DEFAULT_LGD
        assert sat_coeffs["exotic_bond"] == DEFAULT_SAT


class TestLoadConfig:
    def test_returns_none_none_on_failure(self):
        import sys
        mock_admin = MagicMock()
        mock_admin.get_config.side_effect = Exception("no config")
        with patch.dict(sys.modules, {"admin_config": mock_admin}):
            lgd, weights = _load_config()
        assert lgd is None
        assert weights is None

    def test_returns_lgd_from_admin_config(self):
        import sys
        mock_admin = MagicMock()
        mock_admin.get_config.return_value = {
            "model": {"lgd_assumptions": {"mortgage": {"lgd": 0.15}, "personal": {"lgd": 0.50}}},
            "app_settings": {"scenarios": []},
        }
        with patch.dict(sys.modules, {"admin_config": mock_admin}):
            lgd, _ = _load_config()
        assert lgd == {"mortgage": 0.15, "personal": 0.50}

    def test_returns_weights_from_admin_config(self):
        import sys
        mock_admin = MagicMock()
        mock_admin.get_config.return_value = {
            "model": {"lgd_assumptions": {}},
            "app_settings": {
                "scenarios": [
                    {"key": "base", "weight": 0.5},
                    {"key": "adverse", "weight": 0.5},
                ]
            },
        }
        with patch.dict(sys.modules, {"admin_config": mock_admin}):
            _, weights = _load_config()
        assert weights == {"base": 0.5, "adverse": 0.5}

    def test_returns_none_lgd_when_empty(self):
        import sys
        mock_admin = MagicMock()
        mock_admin.get_config.return_value = {
            "model": {"lgd_assumptions": {}},
            "app_settings": {"scenarios": []},
        }
        with patch.dict(sys.modules, {"admin_config": mock_admin}):
            lgd, weights = _load_config()
        assert lgd is None
        assert weights is None

    def test_returns_none_weights_when_no_scenarios(self):
        import sys
        mock_admin = MagicMock()
        mock_admin.get_config.return_value = {
            "model": {"lgd_assumptions": {"m": {"lgd": 0.15}}},
            "app_settings": {},
        }
        with patch.dict(sys.modules, {"admin_config": mock_admin}):
            _, weights = _load_config()
        assert weights is None
