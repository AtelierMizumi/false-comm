"""Unit tests for the i18n localization and translation system."""

from false_comm.i18n.manager import I18nManager, get_locale, set_locale, t


def test_default_locale_is_english() -> None:
    mgr = I18nManager(initial_locale="en")
    assert mgr.locale == "en"
    text = mgr.translate("cli.option_dry_run")
    assert "Simulate and preview" in text


def test_vietnamese_translation() -> None:
    mgr = I18nManager(initial_locale="vi")
    assert mgr.locale == "vi"
    text = mgr.translate("cli.option_dry_run")
    assert "Chạy mô phỏng thử nghiệm" in text


def test_fallback_to_english_on_missing_key() -> None:
    mgr = I18nManager(initial_locale="vi")
    # Non-existent key in Vietnamese should fallback to English or return key
    res = mgr.translate("some.completely.nonexistent.key")
    assert res == "some.completely.nonexistent.key"


def test_parameter_interpolation() -> None:
    mgr = I18nManager(initial_locale="en")
    res = mgr.translate("cli.version", version="2.0.0")
    assert "false-comm version 2.0.0" == res

    mgr.set_locale("vi")
    res_vi = mgr.translate("cli.version", version="2.0.0")
    assert "Phiên bản false-comm 2.0.0" == res_vi


def test_global_helpers() -> None:
    set_locale("en")
    assert get_locale() == "en"
    assert "Operating System" in t("doctor.os_distro")

    set_locale("vi")
    assert get_locale() == "vi"
    assert "Hệ điều hành" in t("doctor.os_distro")

    # Reset back to English
    set_locale("en")
