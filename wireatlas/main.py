import sys

from PySide6.QtWidgets import QApplication

from wireatlas.ui.main_window import MainWindow


def main() -> int:
    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)

    window = MainWindow()
    window.resize(1200, 700)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())