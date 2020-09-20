from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class SIGNAL(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.canvas = FigureCanvas(Figure())
        self.toolbar = NavigationToolbar(self.canvas, self)

        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.toolbar)
        vertical_layout.addWidget(self.canvas)

        self.canvas.axes = self.canvas.figure.add_axes([0.11, 0.2, 0.85, 0.65])
        self.setLayout(vertical_layout)

