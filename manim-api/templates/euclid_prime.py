"""Template: prova de Euclides sobre infinitude de primos.

A cena :class:`EuclidPrime` pode ser renderizada standalone pelo Manim CLI:

    manim render -r 600,400 --fps 30 --write_to_movie --disable_caching \
        manim-api/templates/euclid_prime.py EuclidPrime

Para uso via registry/API, a função :func:`get_source` retorna o código-fonte
parametrizável como string.
"""

import math

from manim import *

_DEFAULT_PRIMES = [2, 3, 5]
_DEFAULT_PRIME_COLOR = "#EF4444"
_DEFAULT_ACCENT_COLOR = "#3B82F6"

_PRODUCT = math.prod(_DEFAULT_PRIMES)
_NEW_NUMBER = _PRODUCT + 1


def _find_factor(primes: list[int], number: int) -> int:
    """Retorna um fator primo de ``number`` que não esteja em ``primes``."""
    for p in primes:
        if number % p == 0:
            return p
    return number


_SCENE_SOURCE_TEMPLATE = """from manim import *
from manim import config

config.background_color = {background_color!r}

class EuclidPrime(Scene):
    def construct(self):
        primes = {primes!r}
        new_prime = {new_number!r}
        found = {found!r}

        product_expr = Text(
            "{product_expr}",
            font_size=52,
            color={accent_color!r},
        )
        product_expr.shift(UP * 0.8)

        note = Text(
            f"{{new_prime}} não é divisível por nenhum dos primos usados",
            font_size=28,
        )
        note.next_to(product_expr, DOWN, buff=0.6)

        conclusion = Text(
            "Portanto existe um novo primo",
            font_size=40,
            color={prime_color!r},
        )
        conclusion.next_to(note, DOWN, buff=0.6)

        self.play(Write(product_expr), run_time=1.5)
        self.wait(0.4)
        self.play(FadeIn(note), run_time=0.8)
        self.wait(0.4)
        self.play(FadeIn(conclusion), run_time=0.8)
        self.wait(0.5)
"""

# Valores padrão computados uma única vez para a cena standalone.
_DEFAULT_SCENE_ARGS = {
    "background_color": "#FFFFFF",
    "primes": _DEFAULT_PRIMES,
    "new_number": _NEW_NUMBER,
    "found": _find_factor(_DEFAULT_PRIMES, _NEW_NUMBER),
    "product_expr": " × ".join(str(p) for p in _DEFAULT_PRIMES) + f" + 1 = {_NEW_NUMBER}",
    "prime_color": _DEFAULT_PRIME_COLOR,
    "accent_color": _DEFAULT_ACCENT_COLOR,
}

exec(_SCENE_SOURCE_TEMPLATE.format(**_DEFAULT_SCENE_ARGS), globals())


def get_source(
    background_color: str = _DEFAULT_SCENE_ARGS["background_color"],
    primes: list[int] | None = None,
    prime_color: str = _DEFAULT_PRIME_COLOR,
    accent_color: str = _DEFAULT_ACCENT_COLOR,
    **kwargs,
) -> tuple[str, str]:
    """Retorna o nome da cena e o código-fonte parametrizado.

    Parameters
    ----------
    background_color
        Cor de fundo da cena (hex).
    primes
        Lista de primos iniciais usados na multiplicação.
    prime_color
        Cor do texto de conclusão (hex).
    accent_color
        Cor da expressão do produto (hex).

    Returns
    -------
    tuple[str, str]
        ``(scene_name, source_code)`` pronto para renderização.
    """
    prime_list = kwargs.get("primes", primes)
    if not isinstance(prime_list, list) or len(prime_list) == 0:
        prime_list = list(_DEFAULT_PRIMES)

    product = math.prod(prime_list)
    new_number = product + 1
    found = _find_factor(prime_list, new_number)
    product_expr = " × ".join(str(p) for p in prime_list) + f" + 1 = {new_number}"

    params = {
        "background_color": kwargs.get("background_color", background_color),
        "primes": prime_list,
        "new_number": new_number,
        "found": found,
        "product_expr": product_expr,
        "prime_color": kwargs.get("prime_color", prime_color),
        "accent_color": kwargs.get("accent_color", accent_color),
    }
    return "EuclidPrime", _SCENE_SOURCE_TEMPLATE.format(**params)
