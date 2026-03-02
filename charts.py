import pyqtgraph as pg
from PyQt6.QtWidgets import QVBoxLayout, QWidget


class ZoneChartsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.temp_plot = pg.PlotWidget()
        self.smoke_plot = pg.PlotWidget()

        self._configure_plot(
            self.temp_plot, "Температура", "Время, с", "Температура, °C"
        )
        self._configure_plot(self.smoke_plot, "Дымность", "Время, с", "Дым, ppm")

        self.temp_curve = self.temp_plot.plot(pen=pg.mkPen("#f57c00", width=2))
        self.smoke_curve = self.smoke_plot.plot(pen=pg.mkPen("#1565c0", width=2))

        layout.addWidget(self.temp_plot)
        layout.addWidget(self.smoke_plot)

    def _configure_plot(self, plot, title, x_label, y_label):
        plot.setBackground("#ffffff")
        plot.showGrid(x=True, y=True, alpha=0.25)
        plot.setTitle(title)
        plot.setLabel("bottom", x_label)
        plot.setLabel("left", y_label)
        plot.setMenuEnabled(False)
        plot.setMouseEnabled(x=True, y=False)

    def set_data(self, temp_values, smoke_values):
        temp_x = list(range(len(temp_values)))
        smoke_x = list(range(len(smoke_values)))
        self.temp_curve.setData(temp_x, list(temp_values))
        self.smoke_curve.setData(smoke_x, list(smoke_values))
