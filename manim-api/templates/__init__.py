"""Biblioteca de templates determinísticos de clipes Manim."""

from .base import ClipTemplate
from .circle_growing import CircleGrowingTemplate
from .ulam_spiral import UlamSpiralTemplate
from .euclid_prime import EuclidPrimeTemplate
from .bar_chart import BarChartTemplate
from .number_line import NumberLineTemplate

__all__ = [
    "ClipTemplate",
    "CircleGrowingTemplate",
    "UlamSpiralTemplate",
    "EuclidPrimeTemplate",
    "BarChartTemplate",
    "NumberLineTemplate",
    "list_templates",
    "get_template",
]

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
