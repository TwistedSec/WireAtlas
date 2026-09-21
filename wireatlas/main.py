import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from wireatlas.ui.main_window import MainWindow


def _create_splash():
    logo_path = (
        Path(__file__).parent
        / "assets"
        / "wireatlas_logo.png"
    )
    pixmap = QPixmap(str(logo_path))

    return QSplashScreen(pixmap)


def _schedule_main_window_show(splash, window) -> None:
    def show_main_window():
        window.show()
        splash.finish(window)

    QTimer.singleShot(3000, show_main_window)


def main() -> int:
    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)

    window = MainWindow()
    window.resize(1200, 700)

    splash = _create_splash()
    splash.show()

    _schedule_main_window_show(splash, window)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())