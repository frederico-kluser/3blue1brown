"""Template: zoom animado sobre uma reta numérica."""

from typing import Any

from .base import ClipTemplate


class NumberLineTemplate(ClipTemplate):
    """Reta numérica horizontal com zoom suave para um intervalo destacado."""

    name = "number_line"
    description = "A number line that zooms into a highlighted interval."

    @classmethod
    def render(
        cls,
        width: int,
        height: int,
        background_color: str,
        fps: int,
        **kwargs: Any,
    ) -> tuple[str, str]:
        scene_name = "NumberLineZoomScene"
        start = float(kwargs.get("start", 0))
        end = float(kwargs.get("end", 10))
        zoom_start = float(kwargs.get("zoom_start", 3))
        zoom_end = float(kwargs.get("zoom_end", 5))
        run_time = float(kwargs.get("run_time", 2.0))
        line_color = kwargs.get("line_color", "#334155")
        accent_color = kwargs.get("accent_color", "#EF4444")

        # Normaliza o intervalo de zoom.
        if zoom_end <= zoom_start:
            zoom_end = zoom_start + 1
        if end <= start:
            end = start + 10

        code = f'''from manim import *

class {scene_name}(Scene):
    def construct(self):
        start = {start}
        end = {end}
        zoom_start = {zoom_start}
        zoom_end = {zoom_end}
        line_color = "{line_color}"
        accent_color = "{accent_color}"

        length = config.frame_width * 0.8
        range_size = end - start
        center0 = (start + end) / 2.0

        def value_to_x(v):
            return (v - center0) / range_size * length

        # Eixo principal.
        axis = Line(LEFT * length / 2, RIGHT * length / 2, color=line_color, stroke_width=4)

        # Ticks e labels principais.
        ticks = VGroup()
        steps = max(2, min(10, int(range_size)))
        for i in range(steps + 1):
            t = start + i * range_size / steps
            x = value_to_x(t)
            tick = Line(DOWN * 0.15, UP * 0.15, color=line_color).shift(RIGHT * x)
            label = Text(str(int(t) if t == int(t) else round(t, 1)), font_size=22)
            label.next_to(tick, DOWN, buff=0.2)
            ticks.add(tick, label)

        # Destaque do intervalo de zoom.
        zs_x = value_to_x(zoom_start)
        ze_x = value_to_x(zoom_end)
        bracket = Line(
            RIGHT * zs_x + UP * 0.35,
            RIGHT * ze_x + UP * 0.35,
            color=accent_color,
            stroke_width=6,
        )
        zoom_label = Text(f"[{{zoom_start}}, {{zoom_end}}]", font_size=26, color=accent_color)
        zoom_label.next_to(bracket, UP, buff=0.15)

        group = VGroup(axis, ticks, bracket, zoom_label)
        group.move_to(ORIGIN)

        # Cálculo do zoom.
        zoom_range = zoom_end - zoom_start
        scale = range_size / zoom_range
        new_center = (zoom_start + zoom_end) / 2.0
        shift_x = -(new_center - center0) / zoom_range * length

        self.play(Create(axis), run_time=0.8)
        self.play(Create(ticks), run_time=0.8)
        self.play(FadeIn(bracket), FadeIn(zoom_label), run_time=0.6)
        self.wait(0.3)
        self.play(
            group.animate.scale(scale).shift(RIGHT * shift_x),
            run_time={run_time},
        )
        self.wait(0.5)
'''
        return scene_name, code
