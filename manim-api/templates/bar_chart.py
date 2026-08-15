"""Template: gráfico de barras animado."""

from typing import Any

from .base import ClipTemplate


class BarChartTemplate(ClipTemplate):
    """Gráfico de barras com labels, valores e cores configuráveis."""

    name = "bar_chart"
    description = "An animated bar chart built from labels and numeric values."

    @classmethod
    def render(
        cls,
        width: int,
        height: int,
        background_color: str,
        fps: int,
        **kwargs: Any,
    ) -> tuple[str, str]:
        scene_name = "BarChartScene"
        labels = kwargs.get("labels", ["A", "B", "C"])
        values = kwargs.get("values", [3, 7, 5])
        colors = kwargs.get(
            "colors",
            ["#3B82F6", "#10B981", "#F59E0B"],
        )
        run_time = float(kwargs.get("run_time", 2.5))

        # Garante listas homogêneas e com valores positivos.
        labels = [str(label) for label in labels[:8]]
        values = [max(0.0, float(v)) for v in values[: len(labels)]]
        while len(values) < len(labels):
            values.append(0.0)
        while len(colors) < len(labels):
            colors.append(colors[len(colors) % len(colors)] if colors else "#3B82F6")

        labels_repr = repr(labels)
        values_repr = repr(values)
        colors_repr = repr(colors)

        code = f'''from manim import *

class {scene_name}(Scene):
    def construct(self):
        labels = {labels_repr}
        values = {values_repr}
        colors = {colors_repr}

        if not values:
            self.wait(0.5)
            return

        max_value = max(values) if max(values) > 0 else 1.0
        n = len(values)
        margin = 0.4
        available_width = config.frame_width * 0.8
        available_height = config.frame_height * 0.7
        bar_width = available_width / (n + (n + 1) * margin)
        spacing = bar_width * margin

        chart = VGroup()
        for i, (label, value, color) in enumerate(zip(labels, values, colors)):
            bar_height = (value / max_value) * available_height
            bar = Rectangle(
                width=bar_width,
                height=bar_height,
                color=color,
                fill_opacity=0.85,
            )
            bar.set_fill(color, opacity=0.85)
            x = -available_width / 2 + spacing + bar_width / 2 + i * (bar_width + spacing)
            y = -config.frame_height / 2 + bar_height / 2 + 0.3
            bar.move_to([x, y, 0])

            value_label = Text(str(int(value) if value == int(value) else value), font_size=24)
            value_label.next_to(bar, UP, buff=0.1)

            name_label = Text(label, font_size=28)
            name_label.next_to(bar, DOWN, buff=0.15)

            group = VGroup(bar, value_label, name_label)
            chart.add(group)

        self.play(*[GrowFromEdge(g[0], DOWN) for g in chart], run_time={run_time})
        self.play(*[FadeIn(label) for g in chart for label in (g[1], g[2])], run_time=0.6)
        self.wait(0.5)
'''
        return scene_name, code
