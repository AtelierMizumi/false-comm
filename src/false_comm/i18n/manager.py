"""Localization and translation management."""

import os
from typing import Any

from false_comm.i18n.catalog import MESSAGES


class I18nManager:
    """Manages active locale, language detection, and message translation."""

    DEFAULT_LOCALE = "en"
    SUPPORTED_LOCALES = ("en", "vi")

    def __init__(self, initial_locale: str | None = None) -> None:
        self._active_locale = initial_locale or self.detect_system_locale()

    @property
    def locale(self) -> str:
        return self._active_locale

    def set_locale(self, locale_code: str) -> None:
        """Set the active language ('en' or 'vi')."""
        normalized = locale_code.lower().split("_")[0].split("-")[0]
        if normalized in self.SUPPORTED_LOCALES:
            self._active_locale = normalized
        else:
            self._active_locale = self.DEFAULT_LOCALE

    def detect_system_locale(self) -> str:
        """Detect locale from environment variables (FALSE_COMM_LANG, LC_ALL, LC_MESSAGES, LANG)."""
        candidate = (
            os.environ.get("FALSE_COMM_LANG")
            or os.environ.get("LC_ALL")
            or os.environ.get("LC_MESSAGES")
            or os.environ.get("LANG")
            or self.DEFAULT_LOCALE
        )
        normalized = candidate.lower().split("_")[0].split("-")[0].split(".")[0]
        return normalized if normalized in self.SUPPORTED_LOCALES else self.DEFAULT_LOCALE

    def translate(self, key: str, **kwargs: Any) -> str:
        """Retrieve localized string with formatted arguments."""
        # Try active locale
        locale_dict = MESSAGES.get(self._active_locale, {})
        template = locale_dict.get(key)

        # Fallback to English
        if template is None and self._active_locale != self.DEFAULT_LOCALE:
            template = MESSAGES.get(self.DEFAULT_LOCALE, {}).get(key)

        # Fallback to key itself
        if template is None:
            return key

        if kwargs:
            try:
                return template.format(**kwargs)
            except Exception:
                return template
        return template


# Global singleton instance
_GLOBAL_I18N = I18nManager()


def t(key: str, **kwargs: Any) -> str:
    """Convenient shortcut for translating a key."""
    return _GLOBAL_I18N.translate(key, **kwargs)


def set_locale(locale_code: str) -> None:
    """Set global active language."""
    _GLOBAL_I18N.set_locale(locale_code)


def get_locale() -> str:
    """Get global active language."""
    return _GLOBAL_I18N.locale
