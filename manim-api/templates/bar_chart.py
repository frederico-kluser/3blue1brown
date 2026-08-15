"""Template: gráfico de barras animado.

A cena :class:`BarChart` pode ser renderizada standalone pelo Manim CLI:

    manim render -r 600,400 --fps 30 --write_to_movie --disable_caching \
        manim-api/templates/bar_chart.py BarChart

Para uso via registry/API, a função :func:`get_source` retorna o código-fonte
parametrizável como string.
"""

from manim import *

_SCENE_SOURCE_TEMPLATE = """from manim import *
from manim import config

config.background_color = {background_color!r}

class BarChart(Scene):
    def construct(self):
        labels = {labels!r}
        values = {values!r}
        colors = {colors!r}

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
                color="#1E293B",
                fill_color=color,
                fill_opacity=0.95,
                stroke_width=2,
            )
            bar.set_fill(color, opacity=0.95)
            bar.set_stroke("#1E293B", width=2)
            x = -available_width / 2 + spacing + bar_width / 2 + i * (bar_width + spacing)
            y = -config.frame_height / 2 + bar_height / 2 + 0.3
            bar.move_to([x, y, 0])

            value_label = Text(
                str(int(value) if value == int(value) else value),
                font_size=28,
                color="#1E293B",
                weight=BOLD,
            )
            value_label.next_to(bar, UP, buff=0.1)

            name_label = Text(label, font_size=30, color="#334155", weight=BOLD)
            name_label.next_to(bar, DOWN, buff=0.15)

            group = VGroup(bar, value_label, name_label)
            chart.add(group)

        self.play(*[GrowFromEdge(g[0], DOWN) for g in chart], run_time={run_time!r})
        self.play(*[FadeIn(label) for g in chart for label in (g[1], g[2])], run_time=0.6)
        self.wait(0.5)
"""

_DEFAULT_LABELS = ["A", "B", "C"]
_DEFAULT_VALUES = [3, 7, 5]
_DEFAULT_COLORS = ["#1E40AF", "#15803D", "#B91C1C"]
_DEFAULT_RUN_TIME = 2.5


def _normalize_chart_data(
    labels: list,
    values: list,
    colors: list,
) -> tuple[list[str], list[float], list[str]]:
    """Normaliza labels, valores e cores para o gráfico."""
    labels = [str(label) for label in labels[:8]]
    values = [max(0.0, float(v)) for v in values[: len(labels)]]
    while len(values) < len(labels):
        values.append(0.0)

    safe_colors = list(colors)
    while len(safe_colors) < len(labels):
        safe_colors.append(
            safe_colors[len(safe_colors) % len(safe_colors)]
            if safe_colors
            else "#3B82F6"
        )
    return labels, values, safe_colors[: len(labels)]


_DEFAULTS = {
    "background_color": "#FFFFFF",
    "labels": _DEFAULT_LABELS,
    "values": _DEFAULT_VALUES,
    "colors": _DEFAULT_COLORS,
    "run_time": _DEFAULT_RUN_TIME,
}

exec(_SCENE_SOURCE_TEMPLATE.format(**_DEFAULTS), globals())


def get_source(
    background_color: str = _DEFAULTS["background_color"],
    labels: list | None = None,
    values: list | None = None,
    colors: list | None = None,
    run_time: float = _DEFAULT_RUN_TIME,
    **kwargs,
) -> tuple[str, str]:
    """Retorna o nome da cena e o código-fonte parametrizado.

    Parameters
    ----------
    background_color
        Cor de fundo da cena (hex).
    labels
        Rótulos das barras.
    values
        Valores numéricos das barras.
    colors
        Cores de cada barra (hex).
    run_time
        Duração da animação de crescimento das barras, em segundos.

    Returns
    -------
    tuple[str, str]
        ``(scene_name, source_code)`` pronto para renderização.
    """
    labels_in = kwargs.get("labels", labels) or list(_DEFAULT_LABELS)
    values_in = kwargs.get("values", values) or list(_DEFAULT_VALUES)
    colors_in = kwargs.get("colors", colors) or list(_DEFAULT_COLORS)

    norm_labels, norm_values, norm_colors = _normalize_chart_data(
        labels_in, values_in, colors_in
    )

    params = {
        "background_color": kwargs.get("background_color", background_color),
        "labels": norm_labels,
        "values": norm_values,
        "colors": norm_colors,
        "run_time": float(kwargs.get("run_time", run_time)),
    }
    return "BarChart", _SCENE_SOURCE_TEMPLATE.format(**params)
