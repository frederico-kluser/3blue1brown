"""Cena determinística: círculo azul crescendo no centro."""

from manim import Circle, Create, Scene


class SimpleShapeScene(Scene):
    def construct(self):
        circle = Circle(radius=1.5, color="#3B82F6")
        circle.set_fill("#3B82F6", opacity=0.5)
        self.play(Create(circle), run_time=1.5)
        self.wait(0.5)
