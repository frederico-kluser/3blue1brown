"""Template: espiral de Ulam destacando números primos."""

from .base import ClipTemplate


class UlamSpiralTemplate(ClipTemplate):
    """Espiral quadrada de Ulam com primos destacados em vermelho."""

    name = "ulam_spiral"
    description = "Ulam spiral highlighting prime numbers among composites."

    @classmethod
    def render(
        cls,
        width: int,
        height: int,
        background_color: str,
        fps: int,
        **kwargs,
    ) -> tuple[str, str]:
        scene_name = "UlamSpiralScene"
        n = int(kwargs.get("n", 200))
        prime_color = kwargs.get("prime_color", "#EF4444")
        composite_color = kwargs.get("composite_color", "#94A3B8")
        run_time = float(kwargs.get("run_time", 2.5))

        code = f'''from manim import *

class {scene_name}(Scene):
    def construct(self):
        n = {n}
        colors = {{"prime": "{prime_color}", "composite": "{composite_color}"}}

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

        self.play(Create(dots), run_time={run_time})
        self.wait(0.5)
'''
        return scene_name, code
