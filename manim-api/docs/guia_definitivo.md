# Guia Técnico: Manim CE 0.19.0 + LLM

## 1. Fundamentos Essenciais
- Use `from manim import *`, uma única classe Scene e `construct(self)`.
- Estruture animações com `self.play(...)`, `self.wait()`, `self.add/remove(...)` e finalize com `self.wait()`.
- Código base:
```python
from manim import *

class Template(Scene):
    def construct(self):
        circle = Circle(color=BLUE, fill_opacity=0.5)
        self.play(Create(circle), run_time=1)
        self.play(circle.animate.shift(RIGHT * 3), run_time=1.5)
        self.wait()
```

## 2. Classes de Scene e quando usar
| Classe | Uso principal | Métodos extras |
|--------|---------------|----------------|
| `Scene` | 2D padrão | `construct`, `play`, `wait`
| `ThreeDScene` | Câmera 3D | `set_camera_orientation`, `begin_ambient_camera_rotation`, `move_camera`
| `MovingCameraScene` | Zoom/pan dinâmico | `self.camera.frame.animate` (move/scale)
| `ZoomedScene` | Inserir janela de zoom | `activate_zooming`, `get_zoom_factor`
| `VectorScene` | Álgebra linear/vetores | Helpers de vetores
| `LinearTransformationScene` | Transformações lineares 2x2 | `apply_matrix`, `apply_inverse`

## 3. Catálogo de Mobjects (resumo)
### Formas básicas
`Circle`, `Dot`, `Ellipse`, `Square`, `Rectangle`, `RoundedRectangle`, `Triangle`, `Polygon`, `RegularPolygon`, `Star`, `Annulus`, `Sector`.

### Linhas e setas
`Line`, `DashedLine`, `Arrow`, `DoubleArrow`, `Vector`, `Angle`, `RightAngle`, `Brace`, `BraceBetweenPoints`.

### Texto/LaTeX
`Text`, `MarkupText`, `Paragraph`, `Tex`, `MathTex`, `Title`, `BulletedList`, `Code`.

### Eixos e gráficos
`Axes`, `ThreeDAxes`, `NumberPlane`, `ComplexPlane`, `PolarPlane`, `NumberLine`, `FunctionGraph`, `ParametricFunction`, `BarChart`. Use `axes.plot`, `axes.c2p/p2c`, `get_area`, `get_vertical_line`, `get_axis_labels`, `get_graph_label`.

### Objetos 3D
`Sphere`, `Cube`, `Cylinder`, `Cone`, `Torus`, `Prism`, `Surface`, `Arrow3D`, `Line3D`, `Dot3D`.

### Utilidades
`VGroup`, `Group`, `Table`, `Matrix`, `DecimalNumber`, `Integer`, `Variable`, `ValueTracker`, `SVGMobject`, `ImageMobject`.

## 4. Animações suportadas
**Criação:** `Create`, `Write`, `DrawBorderThenFill`, `Uncreate`, `Unwrite`, `AddTextLetterByLetter`, `ShowIncreasingSubsets`, `SpiralIn`.

**Transformação:** `Transform`, `ReplacementTransform`, `TransformFromCopy`, `TransformMatchingShapes`, `TransformMatchingTex`, `MoveToTarget`, `ApplyMethod`, `Restore`.

**Fade:** `FadeIn`, `FadeOut`, `FadeTransform`, `FadeTransformPieces`.

**Movimento:** `MoveAlongPath`, `Rotate`, `Rotating`, `Homotopy`, `PhaseFlow`.

**Indicação:** `Indicate`, `Flash`, `Circumscribe`, `ShowPassingFlash`, `FocusOn`, `Wiggle`, `ApplyWave`.

**Crescimento / composição:** `GrowFromCenter`, `GrowFromPoint`, `GrowFromEdge`, `GrowArrow`, `SpinInFromNothing`, `AnimationGroup`, `Succession`, `LaggedStart`, `LaggedStartMap`.

**Utilidades:** `Wait`, `UpdateFromFunc`, `UpdateFromAlphaFunc`, `ChangeDecimalToValue`, `ChangingDecimal`.

## 5. Posicionamento, buffers e cores
- Vetores padrão: `UP`, `DOWN`, `LEFT`, `RIGHT`, `ORIGIN`, `UL`, `UR`, `DL`, `DR`, `IN`, `OUT`.
- Métodos: `.move_to()`, `.shift()`, `.next_to(buff=)`, `.to_edge()`, `.to_corner()`, `.align_to()`, `.arrange()`, `.arrange_in_grid()`.
- Getters: `get_center`, `get_top`, `get_bottom`, `get_left`, `get_right`, `get_edge_center`, `get_corner`, `get_width`, `get_height`.
- Buffers: `SMALL_BUFF`, `MED_SMALL_BUFF`, `MED_LARGE_BUFF`, `LARGE_BUFF`.
- Cores: paletas `BLUE/RED/GREEN/...` + sufixos `_A.._E`, escala `WHITE→BLACK`, `PURE_*`. Ajustes com `set_color`, `set_fill(color, opacity=)`, `set_stroke(color, width=, opacity=)`, `set_color_by_gradient`, `ManimColor.from_hex(hex_str="...")`.

## 6. Configuração e CLI rápida
- Qualidades: `-ql/-qm/-qh/-qp/-qk` (480p → 4K). Use `-p` para preview, `--format gif|mp4|webm|mov`, `-t`/`--transparent` para alfa.
- Resolução personalizada: `-r 1080,1920` ou variáveis `config.pixel_width/pixel_height`; defina `config.frame_rate` conforme necessário.
- Flags úteis: `--media_dir`, `--fps`, `--renderer=opengl`, `--disable_caching`, `-s` (frame final), `-n start,end` (seleção), `--save_last_frame`.
- `manim.cfg`: controla `quality`, `frame_rate`, `media_dir`, `background_color`, `pixel_width/height`, `preview`, `verbosity`.

## 7. Mudanças críticas da versão 0.19.0
- PyAV substitui FFmpeg externo.
- Novidades: cores HSV, animações de digitação, `colorscale` em `plot`, shorthand `@` para `coords_to_point`, log extra em `checkhealth`, suporte Python 3.13.
- Breaking changes: `SurroundingRectangle(..., color=, buff=)`, `ManimColor.from_hex(hex_str=...)`, `Scene.next_section(section_type=...)`, `Axes(x_range=[min, max, step])`.
- Evite `GraphScene`, `TexMobject/TextMobject` e o padrão `CONFIG`.

## 8. Prompt engineering e validação
- Regras fixas: usar Manim CE, import único, nome PascalCase, `construct`, `self.play` para toda animação, `self.wait` final, duração < 30s.
- Sempre usar raw strings pra LaTeX, posicionar objetos explicitamente, garantir texto sobre gráficos (`set_z_index`, `add_background_rectangle`).
- Diferenças CE vs GL: `manim render` vs `manimgl`, `x_range` vs `x_min/x_max`, `hex_str=` em cores, `Scene.next_section(section_type=...)`.
- Parâmetros recomendados para LLM: `temperature 0.0-0.3`, `top_p 0.9-0.95`, `max_tokens` conforme complexidade.
- Checklist pré-render: import válido, classe Scene encontrada, `construct` existe, LaTeX correto, métodos suportados, parâmetros nomeados, sem `opacity` direto em construtores (use `set_fill`/`set_stroke`).

## 9. Exemplos reutilizáveis
### Transformação de equações
```python
class EquationDerivation(Scene):
    def construct(self):
        eq1 = MathTex("{{x}}^2", "+", "{{y}}^2", "=", "{{z}}^2")
        eq2 = MathTex("{{a}}^2", "+", "{{b}}^2", "=", "{{c}}^2")
        eq3 = MathTex("{{a}}^2", "=", "{{c}}^2", "-", "{{b}}^2")
        self.add(eq1)
        self.play(TransformMatchingTex(eq1, eq2))
        self.play(TransformMatchingTex(eq2, eq3))
        self.wait()
```

### Riemann sum
```python
class RiemannSum(Scene):
    def construct(self):
        ax = Axes(x_range=[0, 5], y_range=[0, 6], tips=False)
        curve = ax.plot(lambda x: 4*x - x**2, x_range=[0, 4], color=BLUE_C)
        area = ax.get_riemann_rectangles(curve, x_range=[0.3, 3.7], dx=0.3,
                                         color=BLUE, fill_opacity=0.5)
        self.play(Create(ax), Create(curve), Create(area))
        self.wait()
```

### Cena 3D
```python
class ThreeDRotation(ThreeDScene):
    def construct(self):
        axes = ThreeDAxes()
        sphere = Sphere(radius=1, resolution=(20, 20), fill_opacity=0.3)
        sphere.set_color(BLUE)
        self.set_camera_orientation(phi=75*DEGREES, theta=30*DEGREES)
        self.play(Create(axes), Create(sphere))
        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(5)
        self.stop_ambient_camera_rotation()
        self.move_camera(phi=45*DEGREES, theta=-45*DEGREES)
        self.wait()
```

### MovingCameraScene
```python
class CameraFollow(MovingCameraScene):
    def construct(self):
        self.camera.frame.save_state()
        ax = Axes(x_range=[-1, 10], y_range=[-1, 10])
        graph = ax.plot(lambda x: np.sin(x), color=WHITE, x_range=[0, 3*PI])
        dot_start = Dot(ax.i2gp(graph.t_min, graph))
        dot_end = Dot(ax.i2gp(graph.t_max, graph))
        self.add(ax, graph, dot_start, dot_end)
        self.play(self.camera.frame.animate.scale(0.5).move_to(dot_start))
        self.play(self.camera.frame.animate.move_to(dot_end), run_time=3)
        self.play(Restore(self.camera.frame))
        self.wait()
```

### ValueTracker + always_redraw
```python
class DynamicGraph(Scene):
    def construct(self):
        ax = Axes(x_range=[0, 10], y_range=[0, 100, 10])
        tracker = ValueTracker(0)
        graph = ax.plot(lambda x: 2 * (x - 5) ** 2, color=MAROON)
        dot = always_redraw(lambda: Dot(ax.c2p(tracker.get_value(),
                                              2 * (tracker.get_value() - 5) ** 2)))
        self.add(ax, graph, dot)
        self.play(tracker.animate.set_value(5), run_time=3)
        self.play(tracker.animate.set_value(10), run_time=3)
        self.wait()
```

### Texto com destaque
```python
class TextAnimation(Scene):
    def construct(self):
        title = Text("Manim CE 0.19.0", font_size=72)
        subtitle = Text("Animações Matemáticas", font_size=36).next_to(title, DOWN)
        equation = MathTex(r"e^{i\\pi} + 1 = 0").next_to(subtitle, DOWN)
        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=UP))
        self.play(Write(equation))
        self.play(Indicate(equation))
        self.wait()
```

## 10. Boas práticas adicionais
- Limpe objetos antigos (`FadeOut`, `remove`) para evitar sobreposição.
- Use `always_redraw`/`add_updater` com parcimônia.
- Prefira `Text` para conteúdo simples (mais rápido que `Tex`).
- Para 3D pesado use `--renderer=opengl`.
- Combine `uvicorn main:app --port 8000` + `cloudflared tunnel --url http://localhost:8000` para expor a API.

## 11. Recursos rápidos
- `manim checkhealth` para diagnosticar ambiente.
- Plugins úteis: `manim-voiceover`, `manim-slides`, `ManimML`, `manim-physics`.
- Playground: https://try.manim.community para prototipagem instantânea.
