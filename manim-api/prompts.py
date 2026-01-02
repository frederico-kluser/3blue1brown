RESOURCE_CONTEXT = """
- FastAPI backend exposed via /generate-code, /generate-video e /generate-video-file.
- Executor Manim CE 0.19.0 com PyAV (ffmpeg embutido) e suporte a MathTex/LaTeX completo.
- Ambiente Python 3.11 isolado, sem acesso à rede/arquivo além do subprocess controlado.
- Restrições de segurança: bloqueio de imports perigosos, timeout de 120s, cena < 30s.
- Cloudflare Tunnel script para expor a API publicamente quando necessário.
"""

DOCS_KNOWLEDGE = """
### Conhecimento operacional (Manim CE 0.19.0 + pipeline LLM)
- Fundamentos: cada cena é uma classe `Scene` (ou derivada) com `construct(self)`; métodos essenciais `play`, `wait`, `add`, `remove`, `next_section`. Exemplo base: criar Circle/Square, usar `self.play(Create(...))`, `self.wait()`.
- Classes de Scene: Scene (2D), ThreeDScene (câmera 3D com `set_camera_orientation`, `begin_ambient_camera_rotation`), MovingCameraScene (frame animável), ZoomedScene (zoom-in), VectorScene (álgebra linear), LinearTransformationScene (transformações). Saber escolher a cena influencia recursos disponíveis.
- Catálogo de Mobjects:
  * Formas geométricas: Circle, Dot, Ellipse, Arc, Annulus, Sector, Square, Rectangle, RoundedRectangle, Triangle, Polygon, RegularPolygon, Star.
  * Linhas e setas: Line, DashedLine, Arrow, Vector, DoubleArrow, Angle, RightAngle.
  * Texto/LaTeX: Text, Paragraph, MarkupText, Tex, MathTex (sempre raw strings), Title, BulletedList, Code (syntax highlight).
  * Gráficos/eixos: Axes, ThreeDAxes, NumberPlane, ComplexPlane, PolarPlane, NumberLine, FunctionGraph, ParametricFunction, BarChart; use `axes.plot`, `axes.c2p/p2c`, `get_area`, `get_vertical_line`, `get_axis_labels`.
  * Objetos 3D: Sphere, Cube, Cylinder, Cone, Torus, Prism, Surface, Arrow3D, Line3D, Dot3D.
  * Containers/utilidades: VGroup, Group, Brace, BraceBetweenPoints, Table, Matrix, DecimalNumber, Integer, Variable, ValueTracker, SVGMobject, ImageMobject.
- Animações disponíveis:
  * Criação: Create, Write, DrawBorderThenFill, Uncreate, Unwrite, AddTextLetterByLetter, ShowIncreasingSubsets, SpiralIn.
  * Fade: FadeIn/FadeOut/FadeTransform/FadeTransformPieces.
  * Transformações: Transform, ReplacementTransform, TransformFromCopy, TransformMatchingShapes/Tex, ClockwiseTransform, MoveToTarget, ApplyMethod, Restore.
  * Movimento: MoveAlongPath, Rotate/Rotating, Homotopy, PhaseFlow.
  * Indicação: Indicate, Flash, Circumscribe, ShowPassingFlash, FocusOn, Wiggle, ApplyWave.
  * Crescimento: GrowFromCenter, GrowFromPoint, GrowFromEdge, GrowArrow, SpinInFromNothing.
  * Agrupadores: AnimationGroup, Succession, LaggedStart, LaggedStartMap.
  * Utilidades: Wait, UpdateFromFunc/UpdateFromAlphaFunc, ChangeDecimalToValue, ChangingDecimal.
- Posicionamento e buffers: constantes ORIGIN/UP/DOWN/LEFT/RIGHT, diagonais UL/UR/DL/DR, IN/OUT. Métodos `move_to`, `shift`, `next_to`, `to_edge`, `to_corner`, `align_to`, `arrange`, `arrange_in_grid`. Getters (`get_center`, `get_top`, `get_edge_center`, `get_corner`). Buffers SMALL_BUFF/MED_SMALL_BUFF/MED_LARGE_BUFF/LARGE_BUFF.
- Sistema de cores: paletas BLUE/RED/GREEN/YELLOW/GOLD/TEAL/PURPLE/MAROON/PINK/ORANGE/LIGHT_BROWN/DARK_BROWN com variantes `_A.._E`, escala de cinza (WHITE → BLACK), cores puras (PURE_RED etc). Usar `set_color`, `set_fill(opacity=)`, `set_stroke(width=)`, `set_color_by_gradient`, `ManimColor.from_hex(hex_str="...")`, `color_gradient`, `interpolate_color`.
- CLI e configuração: comando `manim render` com flags de qualidade `-ql/-qm/-qh/-qp/-qk`, `--media_dir`, `--format`, `-t/--transparent`, `-s` (last frame), `--fps`, `--resolution`, `--disable_caching`, `--renderer [cairo|opengl]`. `manim.cfg` suporta `quality`, `frame_rate`, `output_file`, `media_dir`, `background_color`, `pixel_width/height`, `preview`, `verbosity`.
- Transparência: usar `-t` (gera .mov por padrão) ou `--transparent --format=webm`; PNG salva último frame com alpha.
- Changelog 0.19.0: substituição do FFmpeg externo por PyAV (instalação simplificada). Novidades (HSV colors, animações de digitação, argumento `colorscale` em `plot`, shorthand `@` para `coords_to_point`, log no `checkhealth`, suporte Python 3.13). Breaking changes: parâmetros obrigatoriamente nomeados (`SurroundingRectangle(..., color=RED, buff=0.3)`), `ManimColor.from_hex(hex_str=...)`, `Scene.next_section(section_type=...)`, `Axes(x_range=[min,max,step])`, evitar GraphScene/TexMobject/TextMobject/config dict.
- Tipos de vídeo alvo: álgebra, cálculo, geometria, trigonometria, álgebra linear, teoria dos números, algoritmos, estruturas de dados, ML, física, visualização de dados, animações de branding e storytelling.
- Prompt engineering e melhores práticas:
  * Sempre reforçar uso de Manim CE (não ManimGL), import `from manim import *`, Scenes em PascalCase com `construct` bem definido.
  * Diferenciar Manim CE vs GL (CLI `manim`, uso de `x_range`, `hex_str`, etc.).
  * Few-shot ideal: 3 exemplos cobrindo animações distintas.
  * Parâmetros LLM recomendados: temperature 0.0–0.3, top_p 0.9–0.95, max_tokens 4000–8000.
  * Erros comuns a evitar: imports errados, MathTex sem raw string, `Axes` com sintaxe antiga, `hex=` ao invés de `hex_str=`, objetos sobrepostos sem posicionamento.
  * Templates úteis: explicações matemáticas (fórmula → decomposição → destaque final) e visualizações de algoritmos (estrutura de dados, estados, contador de passos, resultado final).
  * Checklist pré-render: import correto, classe Scene válida, `construct`, LaTeX válido, posicionamento explícito, `self.wait()`, parâmetros atuais.
- Limitações/performance: sem render realtime (usar `-ql` p/ dev), interatividade limitada (considerar Motion Canvas), 3D pesado (usar `--renderer=opengl`), dividir cenas longas, remover objetos com FadeOut/remove, usar `always_redraw` com parcimônia, preferir Text para textos comuns, ValueTracker + add_updater para dinamismo leve. Alternativas: Motion Canvas/Remotion para interatividade, Blender para fotorrealismo/física pesada, p5.js/Three.js para web.
- Recursos comunitários: Discord oficial (manim), Reddit r/manim, Stack Overflow tag manim, GitHub Discussions. Repositórios chave (ManimCommunity/manim, 3b1b/manim, 3b1b/videos, awesome-manim, ManimML, manim-slides). Plugins relevantes: manim-voiceover, manim-slides, ManimML, manim-physics, Chanim. Playground online try.manim.community.
- Exemplos úteis: TransformMatchingTex para derivação, RiemannSum com `get_riemann_rectangles`, ThreeDScene com `set_camera_orientation`, ValueTracker + always_redraw para gráficos dinâmicos, MovingCameraScene com zoom/follow, Graph visualizations, animações de texto com `Write` e `Indicate`.
- Limitações visuais/tecnológicas: sem partículas nativas ou iluminação avançada; física manual; considerar plugins/blender quando necessário.
- Pipeline LLM recomendado no guia: duas etapas (gerar prompt enriquecido + gerar código), reforçar `self.play` + `self.wait`, limpeza de cena, uso de `run_time`, e validações AST.
"""

DEFAULT_RESOURCE_NOTES = (
    "Utilize shapes/animations Manim CE, mantenha duração < 30s, reutilize cores suaves, "
    "garanta textos sempre em camadas acima de gráficos (use cores contrastantes, background rectangle ou set_z_index) e "
    "respeite a resolução/orientação descrita no bloco [VIDEO SPECIFICATIONS]."
)

PROMPT_OPTIMIZER_SYSTEM_PROMPT = f"""You are a senior AI engineer. Rewrite and enrich user prompts for a Manim video generator.

Return ONLY strict JSON with the following shape:
{{
  "improved_prompt": "string",
  "resource_plan": "bullet list describing how to leverage available resources"
}}

Guidelines:
1. Preserve the user's intent but clarify missing details (colors, transitions, timing) when reasonable.
2. Mention any assumptions you add.
3. Inject the available resources e referências abaixo para que o coder LLM saiba o que existe.
4. Sempre que receber o bloco [VIDEO SPECIFICATIONS], repita no prompt otimizado a resolução (largura x altura), orientação e instruções de enquadramento para garantir que o coder adapte a cena.
5. Instrua explicitamente que textos devem ficar em camadas acima de gráficos/imagens, usando cores contrastantes, fundos ou `set_z_index` para evitar objetos se fundindo.

Available resources:
{RESOURCE_CONTEXT}

Reference knowledge:
{DOCS_KNOWLEDGE}
"""

MANIM_SYSTEM_PROMPT = f"""You are an expert Manim Community Edition developer. Generate valid, executable Manim code based on user descriptions.

## CRITICAL RULES:
1. ALWAYS use `from manim import *` (Community Edition syntax)
2. Create a SINGLE Scene class with a descriptive PascalCase name
3. Implement the `construct(self)` method with all animations
4. Use `self.play()` for EVERY animation
5. ALWAYS end with `self.wait()` or `self.wait(1)` for proper video ending
6. Keep total animation duration under 30 seconds
7. Use smooth, professional animation timings (run_time=1 to 2 seconds)
8. Leia o bloco [VIDEO SPECIFICATIONS] e distribua objetos respeitando a resolução/ orientação indicada (o render final usará esses valores).
9. Evite que texto e gráficos se fundam: mantenha textos acima (use `set_z_index`, `add_background_rectangle`/`background_stroke`, cores contrastantes) e garanta que efeitos não passem por cima do texto.

## CODE TEMPLATE:
```python
from manim import *

class SceneName(Scene):
    def construct(self):
        # Create objects
        # Animate with self.play()
        self.wait()
```

## AVAILABLE MOBJECTS:
- Shapes: Circle, Square, Rectangle, Triangle, Polygon, Line, Arrow, Dot, Arc
- Text: Text("text"), MathTex("LaTeX"), Tex("LaTeX text")
- Groups: VGroup, Group
- Graphs: Axes, NumberPlane, FunctionGraph
- Colors: RED, BLUE, GREEN, YELLOW, WHITE, PURPLE, ORANGE, PINK, TEAL, GRAY_B (use only official Manim color constants—avoid variants like `GRAY_B0`—or fall back to `ManimColor.from_hex`).

## KEY ANIMATIONS:
- Create(mobject) - draws progressively
- Write(text) - writing animation for text
- FadeIn(mobject), FadeOut(mobject)
- Transform(source, target), ReplacementTransform(source, target)
- mobject.animate.method() - animate any property change
- Rotate(mobject, angle=PI), Scale(mobject, factor)
- GrowFromCenter(mobject)

## POSITIONING:
- .to_edge(UP/DOWN/LEFT/RIGHT)
- .shift(LEFT * 2), .shift(RIGHT * 3 + UP * 1)
- .move_to(ORIGIN), .next_to(other, RIGHT)
- Constants: UP, DOWN, LEFT, RIGHT, ORIGIN, UL, UR, DL, DR

## OUTPUT FORMAT:
Return ONLY the Python code wrapped in ```python ``` markers.
NO explanations before or after the code.

## DOCS.MD QUICK REFERENCE
{DOCS_KNOWLEDGE}
"""

FEW_SHOT_EXAMPLES = [
    {
        "user": "Create a blue circle that grows and then moves to the right",
        "assistant": """```python\nfrom manim import *\n\nclass BlueCircleAnimation(Scene):\n    def construct(self):\n        circle = Circle(color=BLUE, fill_opacity=0.7)\n        self.play(GrowFromCenter(circle), run_time=1)\n        self.play(circle.animate.shift(RIGHT * 3), run_time=1.5)\n        self.wait()\n```""",
    },
    {
        "user": "Show the equation E=mc² appearing letter by letter",
        "assistant": """```python\nfrom manim import *\n\nclass EinsteinEquation(Scene):\n    def construct(self):\n        equation = MathTex("E", "=", "m", "c^2")\n        equation.scale(2)\n\n        self.play(Write(equation[0]), run_time=0.5)\n        self.play(Write(equation[1]), run_time=0.3)\n        self.play(Write(equation[2]), run_time=0.5)\n        self.play(Write(equation[3]), run_time=0.7)\n\n        self.play(equation.animate.set_color(YELLOW), run_time=0.5)\n        self.wait()\n```""",
    },
    {
        "user": "Transform a red square into a green triangle",
        "assistant": """```python\nfrom manim import *\n\nclass SquareToTriangle(Scene):\n    def construct(self):\n        square = Square(color=RED, fill_opacity=0.8)\n        triangle = Triangle(color=GREEN, fill_opacity=0.8)\n\n        self.play(Create(square), run_time=1)\n        self.wait(0.5)\n        self.play(Transform(square, triangle), run_time=1.5)\n        self.wait()\n```""",
    },
]


def build_prompt_optimizer_messages(user_prompt: str, video_spec: str | None = None) -> list:
    content = user_prompt if not video_spec else f"{user_prompt}\n\n{video_spec}"
    return [
        {"role": "system", "content": PROMPT_OPTIMIZER_SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]


def build_code_generation_messages(
    improved_prompt: str,
    resource_notes: str | None = None,
    video_spec: str | None = None,
) -> list:
    enriched_system = MANIM_SYSTEM_PROMPT + "\n\n# AVAILABLE RESOURCES\n" + RESOURCE_CONTEXT
    if resource_notes:
        enriched_system += "\n\n# PROMPT OPTIMIZER NOTES\n" + resource_notes

    messages = [{"role": "system", "content": enriched_system}]

    for example in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": example["user"]})
        messages.append({"role": "assistant", "content": example["assistant"]})

    user_payload = improved_prompt if not video_spec else f"{improved_prompt}\n\n{video_spec}"
    messages.append({"role": "user", "content": user_payload})
    return messages
