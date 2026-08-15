"""Biblioteca de templates determinísticos de clipes Manim.

Cada módulo em :mod:`templates` expõe uma cena Manim standalone (pode ser
renderizada diretamente pelo CLI) e uma função ``get_source`` que retorna o
código-fonte parametrizável. Este pacote encapsula essas cenas em subclasses de
:class:`ClipTemplate` para uso pelo registry/API.
"""

from typing import Any

from .base import ClipTemplate
from .circle_growing import CircleGrowing, get_source as _circle_growing_source
from .ulam_spiral import UlamSpiral, get_source as _ulam_spiral_source
from .euclid_prime import EuclidPrime, get_source as _euclid_prime_source
from .bar_chart import BarChart, get_source as _bar_chart_source
from .number_line import NumberLine, get_source as _number_line_source

__all__ = [
    "ClipTemplate",
    # Cenas Manim standalone
    "CircleGrowing",
    "UlamSpiral",
    "EuclidPrime",
    "BarChart",
    "NumberLine",
    # Templates determinísticos
    "CircleGrowingTemplate",
    "UlamSpiralTemplate",
    "EuclidPrimeTemplate",
    "BarChartTemplate",
    "NumberLineTemplate",
    # Helpers
    "list_templates",
    "get_template",
]


def _make_template(
    name: str,
    description: str,
    source_fn,
) -> type[ClipTemplate]:
    """Cria uma subclasse de ClipTemplate que delega para ``source_fn``."""

    class _Template(ClipTemplate):
        @classmethod
        def render(
            cls,
            width: int,
            height: int,
            background_color: str,
            fps: int,
            **kwargs: Any,
        ) -> tuple[str, str]:
            return source_fn(**kwargs)

    _Template.__name__ = f"{name.title().replace('_', '')}Template"
    _Template.__qualname__ = _Template.__name__
    _Template.name = name
    _Template.description = description
    return _Template


CircleGrowingTemplate = _make_template(
    "circle_growing",
    "A colored circle growing from the center of the screen.",
    _circle_growing_source,
)
UlamSpiralTemplate = _make_template(
    "ulam_spiral",
    "Ulam spiral highlighting prime numbers among composites.",
    _ulam_spiral_source,
)
EuclidPrimeTemplate = _make_template(
    "euclid_prime",
    "Euclid's proof that multiplying primes and adding 1 yields a new prime.",
    _euclid_prime_source,
)
BarChartTemplate = _make_template(
    "bar_chart",
    "An animated bar chart built from labels and numeric values.",
    _bar_chart_source,
)
NumberLineTemplate = _make_template(
    "number_line",
    "A number line that zooms into a highlighted interval.",
    _number_line_source,
)

_TEMPLATE_MAP: dict[str, type[ClipTemplate]] = {
    CircleGrowingTemplate.name: CircleGrowingTemplate,
    UlamSpiralTemplate.name: UlamSpiralTemplate,
    EuclidPrimeTemplate.name: EuclidPrimeTemplate,
    BarChartTemplate.name: BarChartTemplate,
    NumberLineTemplate.name: NumberLineTemplate,
}


def list_templates() -> list[str]:
    """Retorna a lista de nomes de templates disponíveis, ordenada."""
    return sorted(_TEMPLATE_MAP)


def get_template(name: str) -> type[ClipTemplate]:
    """Retorna a classe do template pelo nome.

    Raises
    ------
    KeyError
        Se o nome não corresponder a nenhum template registrado.
    """
    return _TEMPLATE_MAP[name]
