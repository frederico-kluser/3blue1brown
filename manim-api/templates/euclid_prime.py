"""Template: prova de Euclides sobre infinitude de primos."""

import math
from typing import Any

from .base import ClipTemplate


class EuclidPrimeTemplate(ClipTemplate):
    """Demonstração clássica: multiplique primos, some 1 e mostre um novo primo."""

    name = "euclid_prime"
    description = "Euclid's proof that multiplying primes and adding 1 yields a new prime."

    @classmethod
    def render(
        cls,
        width: int,
        height: int,
        background_color: str,
        fps: int,
        **kwargs: Any,
    ) -> tuple[str, str]:
        scene_name = "EuclidPrimeScene"
        primes = kwargs.get("primes", [2, 3, 5])
        if not isinstance(primes, list) or len(primes) == 0:
            primes = [2, 3, 5]

        product = math.prod(primes)
        new_number = product + 1
        prime_color = kwargs.get("prime_color", "#EF4444")
        accent_color = kwargs.get("accent_color", "#3B82F6")

        primes_str = " × ".join(str(p) for p in primes)
        code = f'''from manim import *

class {scene_name}(Scene):
    def construct(self):
        primes = {primes!r}
        product_expr = Text("{primes_str} + 1 = {new_number}", font_size=52, color="{accent_color}")
        product_expr.shift(UP * 0.8)

        new_prime = {new_number}
        # Encontra um fator primo diferente dos usados na multiplicação.
        found = None
        for p in primes:
            if new_prime % p == 0:
                found = p
                break
        if found is None:
            found = new_prime

        note = Text(
            f"{{new_prime}} não é divisível por nenhum dos primos usados",
            font_size=28,
        )
        note.next_to(product_expr, DOWN, buff=0.6)

        conclusion = Text(
            "Portanto existe um novo primo",
            font_size=40,
            color="{prime_color}",
        )
        conclusion.next_to(note, DOWN, buff=0.6)

        self.play(Write(product_expr), run_time=1.5)
        self.wait(0.4)
        self.play(FadeIn(note), run_time=0.8)
        self.wait(0.4)
        self.play(FadeIn(conclusion), run_time=0.8)
        self.wait(0.5)
'''
        return scene_name, code
