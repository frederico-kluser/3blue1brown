"""Template: zoom animado sobre uma reta numérica.

A cena :class:`NumberLine` pode ser renderizada standalone pelo Manim CLI:

    manim render -r 600,400 --fps 30 --write_to_movie --disable_caching \
        manim-api/templates/number_line.py NumberLine

Para uso via registry/API, a função :func:`get_source` retorna o código-fonte
parametrizável como string.
"""

from manim import *

_SCENE_SOURCE_TEMPLATE = """from manim import *
from manim import config

config.background_color = {background_color!r}

class NumberLine(Scene):
    def construct(self):
        start = {start!r}
        end = {end!r}
        zoom_start = {zoom_start!r}
        zoom_end = {zoom_end!r}
        line_color = {line_color!r}
        accent_color = {accent_color!r}

        length = config.frame_width * 0.8
        range_size = end - start
        center0 = (start + end) / 2.0

        def value_to_x(v):
            return (v - center0) / range_size * length

        # Eixo principal.
        axis = Line(LEFT * length / 2, RIGHT * length / 2, color=line_color, stroke_width=10)

        # Ticks e labels principais.
        ticks = VGroup()
        steps = max(2, min(10, int(range_size)))
        for i in range(steps + 1):
            t = start + i * range_size / steps
            x = value_to_x(t)
            tick = Line(DOWN * 0.28, UP * 0.28, color=line_color, stroke_width=7).shift(RIGHT * x)
            label = Text(
                str(int(t) if t == int(t) else round(t, 1)),
                font_size=44,
                color=line_color,
                weight=BOLD,
            )
            label.next_to(tick, DOWN, buff=0.2)
            ticks.add(tick, label)

        # Destaque do intervalo de zoom.
        zs_x = value_to_x(zoom_start)
        ze_x = value_to_x(zoom_end)
        zoom_band = Rectangle(
            width=max(0.1, ze_x - zs_x),
            height=1.4,
            fill_color=accent_color,
            fill_opacity=0.18,
            stroke_width=0,
        )
        zoom_band.move_to(RIGHT * (zs_x + ze_x) / 2)
        bracket = Line(
            RIGHT * zs_x + UP * 0.52,
            RIGHT * ze_x + UP * 0.52,
            color=accent_color,
            stroke_width=12,
        )
        zoom_label = Text(
            f"[{{zoom_start}}, {{zoom_end}}]",
            font_size=46,
            color=accent_color,
            weight=BOLD,
        )
        zoom_label.next_to(bracket, UP, buff=0.15)

        group = VGroup(axis, ticks, zoom_band, bracket, zoom_label)
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
            run_time={run_time!r},
        )
        self.wait(0.5)
"""

_DEFAULT_START = 0.0
_DEFAULT_END = 10.0
_DEFAULT_ZOOM_START = 3.0
_DEFAULT_ZOOM_END = 5.0
_DEFAULT_LINE_COLOR = "#334155"
_DEFAULT_ACCENT_COLOR = "#B91C1C"
_DEFAULT_RUN_TIME = 2.0


def _normalize_interval(
    start: float,
    end: float,
    zoom_start: float,
    zoom_end: float,
) -> tuple[float, float, float, float]:
    """Garante que o intervalo de zoom esteja contido e válido."""
    if end <= start:
        end = start + 10.0
    if zoom_end <= zoom_start:
        zoom_end = zoom_start + 1.0
    return start, end, zoom_start, zoom_end


_DEFAULTS = {
    "background_color": "#FFFFFF",
    "start": _DEFAULT_START,
    "end": _DEFAULT_END,
    "zoom_start": _DEFAULT_ZOOM_START,
    "zoom_end": _DEFAULT_ZOOM_END,
    "line_color": _DEFAULT_LINE_COLOR,
    "accent_color": _DEFAULT_ACCENT_COLOR,
    "run_time": _DEFAULT_RUN_TIME,
}

exec(_SCENE_SOURCE_TEMPLATE.format(**_DEFAULTS), globals())


def get_source(
    background_color: str = _DEFAULTS["background_color"],
    start: float = _DEFAULT_START,
    end: float = _DEFAULT_END,
    zoom_start: float = _DEFAULT_ZOOM_START,
    zoom_end: float = _DEFAULT_ZOOM_END,
    line_color: str = _DEFAULT_LINE_COLOR,
    accent_color: str = _DEFAULT_ACCENT_COLOR,
    run_time: float = _DEFAULT_RUN_TIME,
    **kwargs,
) -> tuple[str, str]:
    """Retorna o nome da cena e o código-fonte parametrizado.

    Parameters
    ----------
    background_color
        Cor de fundo da cena (hex).
    start, end
        Extremos da reta numérica.
    zoom_start, zoom_end
        Intervalo destacado que receberá zoom.
    line_color
        Cor do eixo e ticks (hex).
    accent_color
        Cor do destaque de zoom (hex).
    run_time
        Duração da animação de zoom, em segundos.

    Returns
    -------
    tuple[str, str]
        ``(scene_name, source_code)`` pronto para renderização.
    """
    norm_start, norm_end, norm_zoom_start, norm_zoom_end = _normalize_interval(
        float(kwargs.get("start", start)),
        float(kwargs.get("end", end)),
        float(kwargs.get("zoom_start", zoom_start)),
        float(kwargs.get("zoom_end", zoom_end)),
    )

    params = {
        "background_color": kwargs.get("background_color", background_color),
        "start": norm_start,
        "end": norm_end,
        "zoom_start": norm_zoom_start,
        "zoom_end": norm_zoom_end,
        "line_color": kwargs.get("line_color", line_color),
        "accent_color": kwargs.get("accent_color", accent_color),
        "run_time": float(kwargs.get("run_time", run_time)),
    }
    return "NumberLine", _SCENE_SOURCE_TEMPLATE.format(**params)
