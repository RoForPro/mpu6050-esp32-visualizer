# main.py

import sys
from PyQt5 import QtWidgets
from scripts.ui import MainWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.showMaximized()
    sys.exit(app.exec_())
