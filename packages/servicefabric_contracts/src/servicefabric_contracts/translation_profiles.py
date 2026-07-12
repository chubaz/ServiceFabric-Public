"""Allowlisted, explicit legacy translation profiles."""
from enum import StrEnum
class TranslationProfile(StrEnum):
    LEGACY_STATIC_FRONTEND = "legacy_static_frontend"
    LEGACY_FLASK_SHARED_HOST = "legacy_flask_shared_host"
    LEGACY_PYTHON_PROCESS = "legacy_python_process"
    LEGACY_COMPOSITE_UI_PYTHON = "legacy_composite_ui_python"
    ASSESSMENT_ONLY = "assessment_only"

TEMPLATE_PROFILE = {
    "vite_base": TranslationProfile.LEGACY_STATIC_FRONTEND,
    "react_base": TranslationProfile.LEGACY_STATIC_FRONTEND,
    "flask_base": TranslationProfile.LEGACY_FLASK_SHARED_HOST,
    "data_science_base": TranslationProfile.LEGACY_PYTHON_PROCESS,
    "quant_vite_base": TranslationProfile.LEGACY_COMPOSITE_UI_PYTHON,
}
