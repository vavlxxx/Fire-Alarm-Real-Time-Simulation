import sys

from PyQt6.QtWidgets import QApplication

from ui import FireAlarmWindow


def main():
    app = QApplication(sys.argv)
    window = FireAlarmWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
