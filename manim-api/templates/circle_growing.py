"""Template: círculo crescendo a partir do centro."""

from .base import ClipTemplate


class CircleGrowingTemplate(ClipTemplate):
    """Círculo colorido que cresce suavemente no centro da tela."""

    name = "circle_growing"
    description = "A colored circle growing from the center of the screen."

    @classmethod
    def render(
        cls,
        width: int,
        height: int,
        background_color: str,
        fps: int,
        **kwargs,
    ) -> tuple[str, str]:
        scene_name = "CircleGrowingScene"
        color = kwargs.get("color", "#3B82F6")
        run_time = float(kwargs.get("run_time", 2.0))
        final_radius = float(kwargs.get("final_radius", 2.5))

        code = f'''from manim import *

class {scene_name}(Scene):
    def construct(self):
        # O raio é proporcional à menor dimensão do frame.
        target = min(config.frame_width, config.frame_height) * 0.35
        circle = Circle(radius=0.05, color="{color}")
        circle.set_fill("{color}", opacity=0.5)

        scale_factor = target / 0.05
        self.play(circle.animate.scale(scale_factor), run_time={run_time})
        self.wait(0.5)
'''
        return scene_name, code
