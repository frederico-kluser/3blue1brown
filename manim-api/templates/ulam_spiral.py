"""Template: espiral de Ulam destacando números primos.

A cena :class:`UlamSpiral` pode ser renderizada standalone pelo Manim CLI:

    manim render -r 600,400 --fps 30 --write_to_movie --disable_caching \
        manim-api/templates/ulam_spiral.py UlamSpiral

Para uso via registry/API, a função :func:`get_source` retorna o código-fonte
parametrizável como string.
"""

from manim import *

_SCENE_SOURCE_TEMPLATE = """from manim import *
from manim import config

config.background_color = {background_color!r}

class UlamSpiral(Scene):
    def construct(self):
        n = {n!r}
        colors = {{"prime": {prime_color!r}, "composite": {composite_color!r}}}

        def is_prime(num):
            if num < 2:
                return False
            if num == 2:
                return True
            if num % 2 == 0:
                return False
            limit = int(num ** 0.5)
            for i in range(3, limit + 1, 2):
                if num % i == 0:
                    return False
            return True

        # Gera coordenadas da espiral quadrada.
        x = y = 0
        dirs = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        dir_idx = 0
        segment_length = 1
        segment_passed = 0
        length_increments = 0
        coords = {{1: (0, 0)}}
        for i in range(2, n + 1):
            dx, dy = dirs[dir_idx]
            x += dx
            y += dy
            coords[i] = (x, y)
            segment_passed += 1
            if segment_passed == segment_length:
                segment_passed = 0
                dir_idx = (dir_idx + 1) % 4
                length_increments += 1
                if length_increments % 2 == 1:
                    segment_length += 1

        max_coord = max(max(abs(cx), abs(cy)) for cx, cy in coords.values())
        span = 2 * max_coord + 2
        scale = min(config.frame_width, config.frame_height) / span

        dots = VGroup()
        for i in range(1, n + 1):
            cx, cy = coords[i]
            color = colors["prime"] if is_prime(i) else colors["composite"]
            dot = Dot(
                point=RIGHT * cx * scale + UP * cy * scale,
                radius=0.06 * scale,
                color=color,
            )
            dots.add(dot)

        self.play(Create(dots), run_time={run_time!r})
        self.wait(0.5)
"""

_DEFAULTS = {
    "background_color": "#FFFFFF",
    "n": 200,
    "prime_color": "#EF4444",
    "composite_color": "#94A3B8",
    "run_time": 2.5,
}

exec(_SCENE_SOURCE_TEMPLATE.format(**_DEFAULTS), globals())


def get_source(
    background_color: str = _DEFAULTS["background_color"],
    n: int = _DEFAULTS["n"],
    prime_color: str = _DEFAULTS["prime_color"],
    composite_color: str = _DEFAULTS["composite_color"],
    run_time: float = _DEFAULTS["run_time"],
    **kwargs,
) -> tuple[str, str]:
    """Retorna o nome da cena e o código-fonte parametrizado.

    Parameters
    ----------
    background_color
        Cor de fundo da cena (hex).
    n
        Quantidade de números a desenhar na espiral.
    prime_color
        Cor dos números primos (hex).
    composite_color
        Cor dos números compostos (hex).
    run_time
        Duração da animação de criação dos pontos, em segundos.

    Returns
    -------
    tuple[str, str]
        ``(scene_name, source_code)`` pronto para renderização.
    """
    params = {
        "background_color": kwargs.get("background_color", background_color),
        "n": int(kwargs.get("n", n)),
        "prime_color": kwargs.get("prime_color", prime_color),
        "composite_color": kwargs.get("composite_color", composite_color),
        "run_time": float(kwargs.get("run_time", run_time)),
    }
    return "UlamSpiral", _SCENE_SOURCE_TEMPLATE.format(**params)
