"""Registry de templates determinísticos de clipes Manim."""

from templates import (
    BarChartTemplate,
    CircleGrowingTemplate,
    EuclidPrimeTemplate,
    NumberLineTemplate,
    UlamSpiralTemplate,
)

_TEMPLATE_MAP: dict[str, type] = {
    CircleGrowingTemplate.name: CircleGrowingTemplate,
    UlamSpiralTemplate.name: UlamSpiralTemplate,
    EuclidPrimeTemplate.name: EuclidPrimeTemplate,
    BarChartTemplate.name: BarChartTemplate,
    NumberLineTemplate.name: NumberLineTemplate,
}

# Palavras-chave simples para matching por prompt (em inglês, minúsculas).
_KEYWORDS: dict[str, list[str]] = {
    "circle_growing": ["circle", "grow", "growing", "expand", "expanding", "pulse", "pulse"],
    "ulam_spiral": ["ulam", "spiral", "prime", "primes", "number spiral", "primality"],
    "euclid_prime": ["euclid", "euclidean", "prime", "primes", "proof", "infinite primes"],
    "bar_chart": ["bar", "bars", "chart", "graph", "data", "statistics", "compare"],
    "number_line": ["number line", "numberline", "zoom", "interval", "axis", "real line"],
}


def list_templates() -> list[str]:
    """Retorna os nomes de todos os templates registrados, ordenados."""
    return sorted(_TEMPLATE_MAP)


def get_template(name: str) -> type:
    """Retorna a classe do template pelo nome."""
    if name not in _TEMPLATE_MAP:
        raise KeyError(f"Template não encontrado: {name!r}")
    return _TEMPLATE_MAP[name]


def resolve_by_prompt(prompt: str) -> type | None:
    """Escolhe o template mais adequado para um prompt em inglês.

    O matching é feito por palavras-chave simples. Se nenhuma palavra-chave
    for encontrada, retorna ``None``.
    """
    prompt_lower = prompt.lower()
    scores: dict[str, int] = {name: 0 for name in _TEMPLATE_MAP}

    for name, keywords in _KEYWORDS.items():
        for keyword in keywords:
            if keyword in prompt_lower:
                scores[name] += 1

    best = max(scores, key=lambda k: scores[k])
    return _TEMPLATE_MAP[best] if scores[best] > 0 else None
