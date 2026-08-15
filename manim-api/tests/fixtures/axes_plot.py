"""Cena determinística: eixos com uma parábola."""

from manim import Axes, Create, Dot, Scene


class AxesPlotScene(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-1, 9, 1],
            axis_config={"include_tip": False},
        )
        graph = axes.plot(lambda x: x**2, color="#EF4444")
        self.play(Create(axes), run_time=1.0)
        self.play(Create(graph), run_time=1.5)
        dot = Dot(axes.c2p(2, 4), color="#F59E0B")
        self.play(Create(dot), run_time=0.5)
        self.wait(0.3)
