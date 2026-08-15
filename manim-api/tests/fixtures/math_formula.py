"""Cena determinística: fórmula de Euler com MathTex."""

from manim import MathTex, Scene, Write


class MathFormulaScene(Scene):
    def construct(self):
        formula = MathTex(r"e^{i\pi} + 1 = 0", font_size=96)
        self.play(Write(formula), run_time=1.5)
        self.wait(0.5)
