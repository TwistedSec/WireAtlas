from pathlib import Path

from wireatlas import main as main_module


def test_main_window_waits_three_seconds_for_splash(monkeypatch):
    scheduled = {}

    class FakeTimer:
        @staticmethod
        def singleShot(milliseconds, callback):
            scheduled["milliseconds"] = milliseconds
            scheduled["callback"] = callback


    class FakeSplash:
        def __init__(self):
            self.finished_with = None


        def finish(self, window):
            self.finished_with = window


    class FakeWindow:
        def __init__(self):
            self.shown = False


        def show(self):
            self.shown = True

    monkeypatch.setattr(
        main_module,
        "QTimer",
        FakeTimer,
        raising=False,
    )

    splash = FakeSplash()
    window = FakeWindow()

    main_module._schedule_main_window_show(
        splash,
        window,
    )

    assert scheduled["milliseconds"] == 3000
    assert not window.shown

    scheduled["callback"]()

    assert window.shown
    assert splash.finished_with is window


def test_main_shows_splash_before_scheduling_main_window(monkeypatch):
    calls = {
        "splash_shown": False,
        "scheduled": False,
    }

    class FakeApp:
        def exec(self):
            return 0


    class FakeQApplication:
        @staticmethod
        def instance():
            return FakeApp()


    class FakeSplash:
        def show(self):
            calls["splash_shown"] = True


    class FakeWindow:
        def __init__(self):
            self.shown = False


        def resize(self, width, height):
            pass


        def show(self):
            self.shown = True


    splash = FakeSplash()
    window = FakeWindow()

    monkeypatch.setattr(
        main_module,
        "QApplication",
        FakeQApplication,
    )
    monkeypatch.setattr(
        main_module,
        "_create_splash",
        lambda: splash,
    )
    monkeypatch.setattr(
        main_module,
        "MainWindow",
        lambda: window,
    )


    def fake_schedule(scheduled_splash, scheduled_window):
        calls["scheduled"] = True
        assert scheduled_splash is splash
        assert scheduled_window is window

    monkeypatch.setattr(
        main_module,
        "_schedule_main_window_show",
        fake_schedule,
    )

    result = main_module.main()

    assert result == 0
    assert calls["splash_shown"]
    assert calls["scheduled"]
    assert not window.shown

def test_create_splash_uses_wireatlas_logo(monkeypatch):
    loaded_path = {}

    class FakePixmap:
        def __init__(self, path):
            loaded_path["path"] = path


    class FakeSplash:
        def __init__(self, pixmap):
            self.pixmap = pixmap


    monkeypatch.setattr(
        main_module,
        "QPixmap",
        FakePixmap,
        raising=False,
    )
    monkeypatch.setattr(
        main_module,
        "QSplashScreen",
        FakeSplash,
    )

    splash = main_module._create_splash()

    expected = (
        Path(main_module.__file__).parent
        / "assets"
        / "wireatlas_logo.png"
    )

    assert loaded_path["path"] == str(expected)
    assert splash is not None

def test_main_uses_created_splash(monkeypatch):
    calls = {
        "create_splash": False,
        "splash_shown": False,
    }


    class FakeApp:
        def exec(self):
            return 0


    class FakeQApplication:
        @staticmethod
        def instance():
            return FakeApp()


    class FakeSplash:
        def show(self):
            calls["splash_shown"] = True


    class FakeWindow:
        def resize(self, width, height):
            pass

    splash = FakeSplash()
    window = FakeWindow()

    monkeypatch.setattr(
        main_module,
        "QApplication",
        FakeQApplication,
    )
    monkeypatch.setattr(
        main_module,
        "MainWindow",
        lambda: window,
    )


    def fake_create_splash():
        calls["create_splash"] = True
        return splash

    monkeypatch.setattr(
        main_module,
        "_create_splash",
        fake_create_splash,
    )

    monkeypatch.setattr(
        main_module,
        "_schedule_main_window_show",
        lambda scheduled_splash, scheduled_window: None,
    )

    def fail_if_used_directly(*args, **kwargs):
        raise AssertionError(
            "main() should use _create_splash()"
        )


    monkeypatch.setattr(
        main_module,
        "QSplashScreen",
        fail_if_used_directly,
    )

    result = main_module.main()

    assert result == 0
    assert calls["create_splash"]
    assert calls["splash_shown"]