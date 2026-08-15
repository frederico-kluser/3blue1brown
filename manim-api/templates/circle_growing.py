"""Template: círculo crescendo a partir do centro.

A cena :class:`CircleGrowing` pode ser renderizada standalone pelo Manim CLI:

    manim render -r 600,400 --fps 30 --write_to_movie --disable_caching \
        manim-api/templates/circle_growing.py CircleGrowing

Para uso via registry/API, a função :func:`get_source` retorna o código-fonte
parametrizável como string.
"""

from manim import *

_SCENE_SOURCE_TEMPLATE = """from manim import *
from manim import config

config.background_color = {background_color!r}

class CircleGrowing(Scene):
    def construct(self):
        color = {color!r}
        run_time = {run_time!r}
        target = min(config.frame_width, config.frame_height) * 0.35
        circle = Circle(radius=0.05, color=color)
        circle.set_fill(color, opacity=0.5)

        scale_factor = target / 0.05
        self.play(circle.animate.scale(scale_factor), run_time=run_time)
        self.wait(0.5)
"""

_DEFAULTS = {
    "background_color": "#FFFFFF",
    "color": "#3B82F6",
    "run_time": 2.0,
}

# Define a classe de cena standalone a partir do mesmo template usado por
# get_source(), garantindo que o comportamento padrão seja idêntico.
exec(_SCENE_SOURCE_TEMPLATE.format(**_DEFAULTS), globals())


def get_source(
    background_color: str = _DEFAULTS["background_color"],
    color: str = _DEFAULTS["color"],
    run_time: float = _DEFAULTS["run_time"],
    **kwargs,
) -> tuple[str, str]:
    """Retorna o nome da cena e o código-fonte parametrizado.

    Parameters
    ----------
    background_color
        Cor de fundo da cena (hex).
    color
        Cor do círculo (hex).
    run_time
        Duração da animação de crescimento, em segundos.

    Returns
    -------
    tuple[str, str]
        ``(scene_name, source_code)`` pronto para ser escrito em disco e
        renderizado pelo Manim CLI.
    """
    params = {
        "background_color": kwargs.get("background_color", background_color),
        "color": kwargs.get("color", color),
        "run_time": float(kwargs.get("run_time", run_time)),
    }
    return "CircleGrowing", _SCENE_SOURCE_TEMPLATE.format(**params)
