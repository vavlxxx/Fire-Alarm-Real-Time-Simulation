import tkinter as tk

from simulation import clamp


class LineChart(tk.Frame):
    def __init__(
        self,
        master,
        title,
        y_label,
        y_min,
        y_max,
        line_color,
        bg,
        text_color,
        grid_color,
        width=360,
        height=170,
        max_points=60,
        x_label="Time (s)",
    ):
        super().__init__(master, bg=bg)
        self.title = title
        self.y_label = y_label
        self.y_min = y_min
        self.y_max = y_max
        self.line_color = line_color
        self.bg = bg
        self.text_color = text_color
        self.grid_color = grid_color
        self.width = width
        self.height = height
        self.max_points = max_points
        self.x_label = x_label
        self.canvas = tk.Canvas(self, width=width, height=height, bg=bg, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def draw(self, series):
        values = list(series)
        self.canvas.delete("all")
        canvas_width = max(self.width, self.canvas.winfo_width())
        canvas_height = max(self.height, self.canvas.winfo_height())

        plot_left = 64
        plot_right = canvas_width - 18
        plot_top = 30
        plot_bottom = canvas_height - 36
        plot_width = plot_right - plot_left
        plot_height = plot_bottom - plot_top

        self.canvas.create_text(
            plot_left,
            10,
            text=self.title,
            anchor="w",
            fill=self.text_color,
            font=("Segoe UI", 10, "bold"),
        )
        self.canvas.create_text(
            plot_right,
            10,
            text=self.y_label,
            anchor="e",
            fill=self.text_color,
            font=("Segoe UI", 9),
        )
        self.canvas.create_line(plot_left, plot_top, plot_left, plot_bottom, fill=self.text_color, width=1)
        self.canvas.create_line(plot_left, plot_bottom, plot_right, plot_bottom, fill=self.text_color, width=1)

        for i in range(6):
            y = plot_top + i * (plot_height / 5)
            self.canvas.create_line(plot_left, y, plot_right, y, fill=self.grid_color)
            value = self.y_max - i * (self.y_max - self.y_min) / 5
            self.canvas.create_text(
                plot_left - 8,
                y,
                text=f"{value:.0f}",
                anchor="e",
                fill=self.text_color,
                font=("Segoe UI", 8),
            )

        for i in range(7):
            x = plot_left + i * (plot_width / 6)
            self.canvas.create_line(x, plot_top, x, plot_bottom, fill=self.grid_color)
            self.canvas.create_text(
                x,
                plot_bottom + 10,
                text=str(i * 10),
                anchor="n",
                fill=self.text_color,
                font=("Segoe UI", 8),
            )
        self.canvas.create_text(
            (plot_left + plot_right) / 2,
            canvas_height - 6,
            text=self.x_label,
            anchor="s",
            fill=self.text_color,
            font=("Segoe UI", 8),
        )

        if len(values) < 2:
            return
        points = []
        for i, value in enumerate(values):
            x = plot_left + (plot_width * i / (self.max_points - 1))
            y = plot_bottom - (plot_height * (value - self.y_min) / (self.y_max - self.y_min))
            y = clamp(y, plot_top, plot_bottom)
            points.extend([x, y])
        self.canvas.create_line(points, fill=self.line_color, width=2)
        self.canvas.create_oval(
            points[-2] - 3, points[-1] - 3, points[-2] + 3, points[-1] + 3, fill=self.line_color, outline=""
        )
