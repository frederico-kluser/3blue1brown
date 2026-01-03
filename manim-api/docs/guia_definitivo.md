```# Guia Definitivo: Manim Community Edition 0.19.0 + GPT-4o-mini

**Geração de vídeos animados educacionais via LLM** — um manual completo cobrindo todas as possibilidades, configurações, melhores práticas e integração com modelos de linguagem.

A combinação de Manim Community Edition com GPT-4o-mini representa uma revolução na criação de conteúdo educacional animado. Este guia abrange desde a estrutura fundamental do Manim até técnicas avançadas de prompt engineering, permitindo que desenvolvedores e educadores gerem animações matemáticas de alta qualidade usando inteligência artificial. A versão **0.19.0** trouxe mudanças significativas, incluindo a remoção da dependência do FFmpeg externo em favor do PyAV, simplificando drasticamente a instalação.

---

## Índice

1. [Fundamentos do Manim CE 0.19.0](#1-fundamentos-do-manim-ce-0190)
2. [Classes de Scene disponíveis](#2-classes-de-scene-disponíveis)
3. [Mobjects: Objetos matemáticos completos](#3-mobjects-objetos-matemáticos-completos)
4. [Animações: Catálogo completo](#4-animações-catálogo-completo)
5. [Sistema de posicionamento e cores](#5-sistema-de-posicionamento-e-cores)
6. [Configuração e CLI](#6-configuração-e-cli)
7. [Changelog v0.19.0 e breaking changes](#7-changelog-v0190-e-breaking-changes)
8. [Tipos de vídeos possíveis](#8-tipos-de-vídeos-possíveis)
9. [Integração GPT-4o-mini: Prompt engineering](#9-integração-gpt-4o-mini-prompt-engineering)
10. [Exemplos de código por categoria](#10-exemplos-de-código-por-categoria)
11. [Limitações e workarounds](#11-limitações-e-workarounds)
12. [Recursos da comunidade](#12-recursos-da-comunidade)
13. [Referência rápida e cheatsheets](#13-referência-rápida-e-cheatsheets)

---

## 1. Fundamentos do Manim CE 0.19.0

### Estrutura básica de uma animação

Toda animação Manim segue um padrão consistente: uma classe que herda de `Scene` com um método `construct()` que define a lógica da animação.

```python
from manim import *

class MinhaAnimacao(Scene):
    def construct(self):
        # Criar objetos
        circulo = Circle(color=BLUE, fill_opacity=0.5)
        
        # Animar
        self.play(Create(circulo))
        self.wait(1)
        
        # Transformar
        quadrado = Square(color=RED)
        self.play(Transform(circulo, quadrado))
        self.wait()
```

### Métodos fundamentais da Scene

| Método | Descrição | Exemplo |
|--------|-----------|---------|
| `construct(self)` | Método principal onde a animação é definida | Obrigatório em toda Scene |
| `play(*animations)` | Executa animações com parâmetros opcionais | `self.play(Create(obj), run_time=2)` |
| `wait(duration)` | Pausa por N segundos | `self.wait(0.5)` |
| `add(*mobjects)` | Adiciona objetos à cena (sem animação) | `self.add(circulo)` |
| `remove(*mobjects)` | Remove objetos da cena | `self.remove(circulo)` |
| `next_section(name)` | Cria seções para apresentações | `self.next_section("intro")` |

---

## 2. Classes de Scene disponíveis

O Manim oferece diferentes tipos de Scene para casos de uso específicos:

| Classe | Uso | Métodos especiais |
|--------|-----|-------------------|
| **Scene** | Base para todas as animações 2D | `construct()`, `play()`, `wait()` |
| **ThreeDScene** | Cenas 3D com câmera tridimensional | `set_camera_orientation(phi, theta, gamma)`, `begin_ambient_camera_rotation()` |
| **MovingCameraScene** | Câmera que pode mover e dar zoom | `self.camera.frame.animate.move_to()`, `.set(width=...)` |
| **ZoomedScene** | Displays de zoom-in | `activate_zooming()`, `get_zoom_factor()` |
| **VectorScene** | Visualizações de vetores | Ideal para álgebra linear |
| **LinearTransformationScene** | Transformações lineares em espaços vetoriais | Visualização de matrizes |

### Exemplo ThreeDScene

```python
class Cena3D(ThreeDScene):
    def construct(self):
        axes = ThreeDAxes()
        esfera = Sphere(radius=1, resolution=(20, 20))
        esfera.set_color(BLUE)
        
        self.set_camera_orientation(phi=75*DEGREES, theta=30*DEGREES)
        self.add(axes, esfera)
        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(5)
        self.stop_ambient_camera_rotation()
```

---

## 3. Mobjects: Objetos matemáticos completos

### Formas geométricas básicas

| Classe | Descrição | Parâmetros principais |
|--------|-----------|----------------------|
| `Circle` | Círculo | `radius`, `color`, `fill_opacity` |
| `Dot` | Ponto pequeno | `point`, `radius`, `color` |
| `Ellipse` | Elipse | `width`, `height` |
| `Arc` | Arco circular | `radius`, `start_angle`, `angle` |
| `Annulus` | Anel (região entre dois círculos) | `inner_radius`, `outer_radius` |
| `Sector` | Fatia de pizza | `outer_radius`, `angle` |

### Polígonos e formas

| Classe | Descrição | Parâmetros principais |
|--------|-----------|----------------------|
| `Square` | Quadrado | `side_length` |
| `Rectangle` | Retângulo | `width`, `height` |
| `RoundedRectangle` | Retângulo com cantos arredondados | `corner_radius`, `width`, `height` |
| `Triangle` | Triângulo equilátero | Tamanho padrão |
| `Polygon` | Polígono qualquer | `*vertices` |
| `RegularPolygon` | Polígono regular de N lados | `n` (número de lados) |
| `Star` | Estrela | `n` (pontas), `outer_radius`, `inner_radius` |

### Linhas e setas

| Classe | Descrição | Parâmetros principais |
|--------|-----------|----------------------|
| `Line` | Linha reta | `start`, `end` |
| `DashedLine` | Linha tracejada | `start`, `end`, `dash_length` |
| `Arrow` | Seta | `start`, `end`, `buff` |
| `Vector` | Vetor a partir da origem | `direction` |
| `DoubleArrow` | Seta dupla | `start`, `end` |
| `Angle` | Arco representando ângulo | `line1`, `line2`, `radius` |
| `RightAngle` | Indicador de ângulo reto | `line1`, `line2`, `length` |

### Texto e matemática

| Classe | Descrição | Parâmetros principais |
|--------|-----------|----------------------|
| `Text` | Texto simples (Pango) | `text`, `font`, `font_size`, `color` |
| `Paragraph` | Texto multilinha | `*text_strings`, `line_spacing` |
| `MarkupText` | Texto com markup Pango | `text` |
| `Tex` | LaTeX modo texto | `*tex_strings` |
| `MathTex` | LaTeX modo matemático | `*tex_strings` |
| `Title` | Título centralizado | `*text_parts` |
| `BulletedList` | Lista com bullets | `*items` |
| `Code` | Código com syntax highlighting | `code`, `language`, `tab_width` |

### Gráficos e eixos

| Classe | Descrição | Parâmetros principais |
|--------|-----------|----------------------|
| `Axes` | Eixos 2D | `x_range`, `y_range`, `x_length`, `y_length` |
| `ThreeDAxes` | Eixos 3D | `x_range`, `y_range`, `z_range` |
| `NumberPlane` | Plano cartesiano com grid | `x_range`, `y_range` |
| `ComplexPlane` | Plano de números complexos | `x_range`, `y_range` |
| `PolarPlane` | Sistema de coordenadas polares | `azimuth_step`, `size` |
| `NumberLine` | Linha numérica única | `x_range`, `length`, `include_numbers` |
| `FunctionGraph` | Gráfico de y=f(x) | `function`, `x_range`, `color` |
| `ParametricFunction` | Curva paramétrica | `function`, `t_range` |
| `BarChart` | Gráfico de barras | `values`, `bar_names` |

#### Métodos importantes do CoordinateSystem

```python
axes = Axes(x_range=[-3, 3, 1], y_range=[-2, 2, 1])

# Plotar função
grafico = axes.plot(lambda x: x**2, color=BLUE)

# Converter coordenadas
ponto = axes.coords_to_point(2, 4)  # ou axes.c2p(2, 4)
coords = axes.point_to_coords(ponto)  # ou axes.p2c(ponto)

# Labels
labels = axes.get_axis_labels(x_label="x", y_label="f(x)")
graph_label = axes.get_graph_label(grafico, label="x^2")

# Área sob o gráfico
area = axes.get_area(grafico, x_range=[0, 2], color=BLUE, opacity=0.5)

# Linha vertical
linha = axes.get_vertical_line(axes.c2p(2, 4))
```

### Objetos 3D

| Classe | Descrição | Parâmetros principais |
|--------|-----------|----------------------|
| `Sphere` | Esfera 3D | `radius`, `resolution`, `u_range`, `v_range` |
| `Cube` | Cubo 3D | `side_length`, `fill_opacity` |
| `Cylinder` | Cilindro 3D | `radius`, `height`, `direction` |
| `Cone` | Cone 3D | `base_radius`, `height` |
| `Torus` | Toro (rosquinha) | `major_radius`, `minor_radius` |
| `Prism` | Prisma retangular | `dimensions=[x, y, z]` |
| `Surface` | Superfície paramétrica | `func`, `u_range`, `v_range`, `resolution` |
| `Arrow3D` | Seta 3D | `start`, `end` |
| `Line3D` | Linha 3D | `start`, `end` |
| `Dot3D` | Ponto 3D | `point`, `radius` |

### Utilitários e containers

| Classe | Descrição |
|--------|-----------|
| `VGroup` | Grupo de VMobjects (vetorizados) |
| `Group` | Grupo de qualquer Mobject |
| `Brace` | Chave curva |
| `BraceBetweenPoints` | Chave entre dois pontos |
| `Table` | Layout de tabela |
| `Matrix` | Display de matriz |
| `DecimalNumber` | Número decimal animável |
| `Integer` | Inteiro animável |
| `Variable` | Variável com label e value tracker |
| `SVGMobject` | Carregar arquivos SVG |
| `ImageMobject` | Exibir imagens |
| `ValueTracker` | Rastrear valores numéricos para animações |

---

## 4. Animações: Catálogo completo

### Animações de criação

| Animação | Descrição | Uso |
|----------|-----------|-----|
| `Create` | Desenha o stroke do VMobject | `self.play(Create(circulo))` |
| `Write` | Escreve texto/LaTeX | `self.play(Write(equacao))` |
| `DrawBorderThenFill` | Desenha borda, depois preenche | `self.play(DrawBorderThenFill(forma))` |
| `Uncreate` | Reverso de Create | `self.play(Uncreate(circulo))` |
| `Unwrite` | Reverso de Write | `self.play(Unwrite(texto))` |
| `AddTextLetterByLetter` | Digita caractere por caractere | `self.play(AddTextLetterByLetter(texto))` |
| `ShowIncreasingSubsets` | Mostra partes incrementalmente | `self.play(ShowIncreasingSubsets(grupo))` |
| `SpiralIn` | Espiral para posição | `self.play(SpiralIn(obj))` |

### Animações de fade

| Animação | Descrição | Parâmetros |
|----------|-----------|------------|
| `FadeIn` | Fade in | `shift`, `target_position`, `scale` |
| `FadeOut` | Fade out | `shift`, `target_position`, `scale` |
| `FadeTransform` | Fade entre dois mobjects | `mobject`, `target_mobject` |
| `FadeTransformPieces` | Fade transform submobjects | `mobject`, `target_mobject` |

### Animações de transformação

| Animação | Descrição | Uso |
|----------|-----------|-----|
| `Transform` | Transforma um mobject em outro | `self.play(Transform(a, b))` |
| `ReplacementTransform` | Transforma e substitui na cena | `self.play(ReplacementTransform(a, b))` |
| `TransformFromCopy` | Transforma uma cópia | `self.play(TransformFromCopy(a, b))` |
| `TransformMatchingShapes` | Combina por similaridade de forma | `self.play(TransformMatchingShapes(a, b))` |
| `TransformMatchingTex` | Combina por tex_string | `self.play(TransformMatchingTex(eq1, eq2))` |
| `ClockwiseTransform` | Transforma no sentido horário | `self.play(ClockwiseTransform(a, b))` |
| `MoveToTarget` | Move para target salvo | `obj.generate_target(); self.play(MoveToTarget(obj))` |
| `ApplyMethod` | Aplica método como animação | `self.play(ApplyMethod(obj.shift, UP))` |
| `Restore` | Restaura estado salvo | `obj.save_state(); self.play(Restore(obj))` |

### Animações de movimento

| Animação | Descrição | Parâmetros |
|----------|-----------|------------|
| `MoveAlongPath` | Move ao longo de um caminho | `mobject`, `path` |
| `Rotate` | Rotaciona mobject | `angle`, `axis`, `about_point` |
| `Rotating` | Rotação contínua | `radians`, `run_time` |
| `Homotopy` | Aplica função homotopia | `homotopy_func`, `mobject` |
| `PhaseFlow` | Fluxo ao longo de campo vetorial | `function`, `mobject` |

### Animações de indicação

| Animação | Descrição | Parâmetros |
|----------|-----------|------------|
| `Indicate` | Destaca temporariamente | `scale_factor`, `color` |
| `Flash` | Efeito flash | `point`, `color`, `num_lines` |
| `Circumscribe` | Desenha ao redor | `shape` (Circle/Rectangle) |
| `ShowPassingFlash` | Flash ao longo do caminho | `time_width` |
| `FocusOn` | Efeito de foco zoom | `opacity` |
| `Wiggle` | Efeito de tremida | `scale_value` |
| `ApplyWave` | Distorção de onda | `direction`, `amplitude` |

### Animações de crescimento

| Animação | Descrição | Uso |
|----------|-----------|-----|
| `GrowFromCenter` | Cresce do centro | `self.play(GrowFromCenter(obj))` |
| `GrowFromPoint` | Cresce de ponto específico | `self.play(GrowFromPoint(obj, point))` |
| `GrowFromEdge` | Cresce da borda | `self.play(GrowFromEdge(obj, UP))` |
| `GrowArrow` | Cresce seta da cauda | `self.play(GrowArrow(arrow))` |
| `SpinInFromNothing` | Gira entrando do zero | `self.play(SpinInFromNothing(obj))` |

### Animações de composição

```python
# AnimationGroup - executa animações juntas
self.play(AnimationGroup(
    Create(circulo),
    Write(texto),
    lag_ratio=0.5  # Início escalonado
))

# Succession - executa em sequência
self.play(Succession(
    Create(circulo),
    Transform(circulo, quadrado),
    FadeOut(circulo)
))

# LaggedStart - início escalonado
self.play(LaggedStart(*[Create(c) for c in circulos], lag_ratio=0.2))

# LaggedStartMap - aplica animação a grupo com lag
self.play(LaggedStartMap(FadeIn, grupo, lag_ratio=0.1))
```

### Animações especiais

| Animação | Descrição |
|----------|-----------|
| `Wait` | Pausa sem operação |
| `UpdateFromFunc` | Atualiza via função |
| `UpdateFromAlphaFunc` | Atualiza via função alpha (0→1) |
| `ChangeDecimalToValue` | Anima mudança de decimal |
| `ChangingDecimal` | Decimal mudando continuamente |

---

## 5. Sistema de posicionamento e cores

### Constantes de direção

```python
# Constantes fundamentais
ORIGIN = np.array([0., 0., 0.])
UP = np.array([0., 1., 0.])
DOWN = np.array([0., -1., 0.])
RIGHT = np.array([1., 0., 0.])
LEFT = np.array([-1., 0., 0.])

# Combinações diagonais
UL = UP + LEFT      # Upper Left
UR = UP + RIGHT     # Upper Right
DL = DOWN + LEFT    # Down Left
DR = DOWN + RIGHT   # Down Right

# 3D
IN = np.array([0., 0., -1.])   # Para dentro da tela
OUT = np.array([0., 0., 1.])   # Para fora da tela
```

### Métodos de posicionamento

| Método | Descrição | Exemplo |
|--------|-----------|---------|
| `move_to(point)` | Move centro para ponto | `obj.move_to(LEFT * 2)` |
| `shift(*vectors)` | Deslocamento relativo | `obj.shift(UP + RIGHT)` |
| `next_to(mob, direction, buff)` | Posiciona próximo a mobject | `obj.next_to(outro, RIGHT, buff=0.5)` |
| `to_edge(edge, buff)` | Move para borda da tela | `obj.to_edge(UP)` |
| `to_corner(corner, buff)` | Move para canto | `obj.to_corner(UL)` |
| `align_to(mob, direction)` | Alinha borda | `obj.align_to(outro, LEFT)` |
| `arrange(*directions, buff)` | Arranja submobjects | `grupo.arrange(RIGHT, buff=0.5)` |
| `arrange_in_grid(rows, cols)` | Arranjo em grid | `grupo.arrange_in_grid(rows=2)` |

### Métodos getter

```python
obj.get_center()           # Ponto central
obj.get_top()              # Centro do topo
obj.get_bottom()           # Centro da base
obj.get_left()             # Centro esquerdo
obj.get_right()            # Centro direito
obj.get_corner(UR)         # Canto específico
obj.get_edge_center(UP)    # Centro da borda
obj.get_width()            # Largura
obj.get_height()           # Altura
```

### Sistema de cores

#### Cores principais (com variantes A-E)

```python
# Variantes: _A (mais claro) até _E (mais escuro), _C é padrão
BLUE, BLUE_A, BLUE_B, BLUE_C, BLUE_D, BLUE_E
RED, RED_A, RED_B, RED_C, RED_D, RED_E
GREEN, GREEN_A, GREEN_B, GREEN_C, GREEN_D, GREEN_E
YELLOW, YELLOW_A, YELLOW_B, YELLOW_C, YELLOW_D, YELLOW_E
GOLD, GOLD_A, GOLD_B, GOLD_C, GOLD_D, GOLD_E
TEAL, TEAL_A, TEAL_B, TEAL_C, TEAL_D, TEAL_E
PURPLE, PURPLE_A, PURPLE_B, PURPLE_C, PURPLE_D, PURPLE_E
MAROON, MAROON_A, MAROON_B, MAROON_C, MAROON_D, MAROON_E
PINK, ORANGE, LIGHT_BROWN, DARK_BROWN

# Escala de cinza
WHITE, GRAY_A, GRAY_B, GRAY_C (GRAY), GRAY_D, GRAY_E, BLACK

# Cores puras
PURE_RED, PURE_GREEN, PURE_BLUE
```

#### Métodos de cor

```python
obj.set_color(BLUE)                        # Cor geral
obj.set_fill(RED, opacity=0.5)             # Preenchimento
obj.set_stroke(WHITE, width=2, opacity=1)  # Contorno
obj.set_color_by_gradient(RED, BLUE)       # Gradiente
obj.set_opacity(0.7)                       # Opacidade geral

# Cores customizadas
from manim import ManimColor
cor = ManimColor.from_hex(hex_str="#FF5733")

# Gradientes
from manim import color_gradient, interpolate_color
cores = color_gradient([RED, BLUE], 5)  # Lista de 5 cores
meio = interpolate_color(RED, BLUE, 0.5)  # Cor do meio
```

---

## 6. Configuração e CLI

### Comando manim render

```bash
manim [OPTIONS] FILE [SCENE_NAMES]...
```

#### Flags de qualidade

| Flag | Qualidade | Resolução | FPS | Uso |
|------|-----------|-----------|-----|-----|
| `-ql` | Low | 854×480 | 15 | Prototipagem rápida |
| `-qm` | Medium | 1280×720 | 30 | Previews, web |
| `-qh` | High | 1920×1080 | 60 | YouTube, apresentações |
| `-qp` | Production | 2560×1440 | 60 | Alta qualidade |
| `-qk` | 4K | 3840×2160 | 60 | Profissional, cinema |

#### Flags de output

| Flag | Descrição |
|------|-----------|
| `-o, --output_file` | Nome do arquivo de saída |
| `--media_dir PATH` | Diretório para vídeos renderizados |
| `--format [png|gif|mp4|webm|mov]` | Formato de saída |
| `-s, --save_last_frame` | Salva apenas último frame como PNG |
| `-t, --transparent` | Background transparente |
| `-r, --resolution "W,H"` | Resolução customizada |
| `--fps FLOAT` | Frame rate customizado |

#### Flags de controle

| Flag | Descrição |
|------|-----------|
| `-p, --preview` | Preview após renderização |
| `-f, --show_in_file_browser` | Abre no explorador de arquivos |
| `-n START,END` | Renderiza animações específicas |
| `-a, --write_all` | Renderiza todas as cenas |
| `--disable_caching` | Desabilita cache |
| `--flush_cache` | Limpa cache antes de renderizar |
| `--renderer [cairo|opengl]` | Backend de renderização |

### Arquivo manim.cfg

Localizações (precedência menor → maior):
1. Library-wide (padrão do Manim)
2. User-wide (`~/.config/manim/manim.cfg`)
3. Folder-wide (`manim.cfg` no diretório do script)

```ini
[CLI]
# Qualidade
quality = high_quality
frame_rate = 60

# Output
output_file = minha_animacao
media_dir = ./media
format = mp4

# Background
background_color = BLACK
background_opacity = 1.0

# Caching
disable_caching = False
max_files_cached = 100

# Preview
preview = True
progress_bar = display

# Logging
verbosity = INFO
log_to_file = False

# LaTeX
no_latex_cleanup = False

# Resolução customizada (para vídeos verticais)
pixel_width = 1080
pixel_height = 1920
```

### Transparência

```bash
# CLI - automaticamente usa .mov
manim -t scene.py MinhaScene

# Ou especificar formato
manim --transparent --format=webm scene.py MinhaScene
```

| Formato | Suporte transparência | Notas |
|---------|----------------------|-------|
| `.mov` | ✅ Sim (ProRes 4444) | Padrão para renders transparentes |
| `.webm` | ✅ Sim (VP9 Alpha) | Boa compatibilidade web |
| `.gif` | ✅ Sim | Paleta de cores limitada |
| `.mp4` | ❌ Não | Não suporta canal alpha |
| `.png` | ✅ Sim | Apenas último frame |

---

## 7. Changelog v0.19.0 e breaking changes

### Mudança principal: FFmpeg → PyAV

A maior mudança na v0.19.0 é a **substituição da dependência externa do ffmpeg pela biblioteca `pyav`**. Usuários não precisam mais instalar ffmpeg separadamente — basta `pip install manim`.

### Novas funcionalidades

- **Classe de cor HSV** com suporte para espaços de cores customizados (PR #3518)
- **Três animações de digitação** simulando typing (PR #3612)
- **Argumento `colorscale`** para `CoordinateSystem.plot()` (PR #3148)
- **Shorthand `@`** para `Axes.coords_to_point()` e `Axes.point_to_coords()` (PR #3754)
- **Log de tempo de execução** no comando checkhealth (PR #3855)
- **Suporte Python 3.13**

### Breaking changes críticos

```python
# ❌ ANTIGO (erro em 0.19.0+):
SurroundingRectangle(mobject, RED, 0.3)
ManimColor.from_hex(hex="#FF0000")
Scene.next_section(type="intro")

# ✅ NOVO (correto):
SurroundingRectangle(mobject, color=RED, buff=0.3)
ManimColor.from_hex(hex_str="#FF0000")
Scene.next_section(section_type="intro")
```

### Mudanças de type aliases

```python
# Renomeados:
# InternalPoint3D → Point3D
# Point3D → Point3DLike
```

### Code mobject reescrito

A implementação do `Code` mobject foi completamente reescrita com mudanças de interface:
- `Code.styles_list` substituído por `Code.get_styles_list()`

### Features deprecadas para evitar

```python
# Evitar em v0.19.0+:
# - GraphScene (usar Axes)
# - TexMobject/TextMobject (usar Tex/MathTex)
# - Padrão CONFIG dict (usar parâmetros __init__)
```

---

## 8. Tipos de vídeos possíveis

### Educação matemática

- **Álgebra**: Equações, desigualdades, funções, sistemas
- **Cálculo**: Derivadas, integrais, limites, séries, Riemann sums
- **Geometria**: Provas, construções, transformações
- **Trigonometria**: Círculo unitário, identidades, gráficos
- **Álgebra linear**: Vetores, matrizes, transformações lineares
- **Teoria dos números**: Visualizações de conceitos numéricos

### Ciência da computação

- **Algoritmos de ordenação**: Bubble, merge, quick, heap sort
- **Algoritmos de busca**: Binary search, BFS, DFS
- **Estruturas de dados**: Árvores, grafos, listas ligadas, pilhas, filas
- **Análise de complexidade**: Big O visualizado
- **Redes neurais**: Arquiteturas, forward pass (com ManimML)
- **Machine learning**: Conceitos visuais

### Física

- **Cinemática**: Movimento, projéteis
- **Ondas e oscilações**: Propagação, interferência
- **Eletromagnetismo**: Campos, forças
- **Óptica**: Reflexão, refração
- **Termodinâmica**: Processos, ciclos
- **Mecânica quântica**: Visualizações conceituais

### Visualização de dados

- **Gráficos animados**: Barras, linhas, pizza
- **Distribuições estatísticas**: Normal, Poisson, etc.
- **Séries temporais**: Animações de evolução
- **Comparações**: Side-by-side animados
- **Infográficos**: Narrativas visuais

### Outros

- **Animações de logo e branding**
- **Slides de apresentação** (com manim-slides)
- **Storytelling visual**
- **Arte generativa abstrata**

---

## 9. Integração GPT-4o-mini: Prompt engineering

### System prompt otimizado

```
Você é um programador Python especialista em criar animações educacionais usando Manim Community Edition (versão 0.19.0).

REQUISITOS CRÍTICOS DE VERSÃO:
- Use Manim Community Edition (ManimCE), NÃO ManimGL
- Import: `from manim import *`
- Scene class: herda de `Scene`
- Versão estável atual: 0.19.0

ESTRUTURA DO CÓDIGO:
1. Sempre use `from manim import *` (nunca `from manimlib import *`)
2. Classes Scene devem herdar de `Scene`
3. Use método `construct(self)` para lógica de animação
4. Use `self.play()` para animações, `self.add()` para elementos estáticos
5. Sempre inclua `self.wait()` para ritmo

BOAS PRÁTICAS DE ANIMAÇÃO:
- Evite sobreposição de elementos - posicione objetos cuidadosamente
- Implemente limpeza de cena usando `self.remove()` ou `FadeOut()`
- Adicione chamadas wait() apropriadas (0.5-2 segundos)
- Mantenha estilo de animação consistente
- Use parâmetro `run_time` para controlar duração

LATEX/MATH:
- Use `MathTex(r"...")` para modo matemático
- Use `Tex(r"...")` para texto com algum LaTeX
- SEMPRE use raw strings (r"...") para LaTeX
- Garanta chaves {} balanceadas em expressões LaTeX

CORES (Manim CE):
- Use: RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, WHITE, BLACK, GRAY, PINK, TEAL
- Para cores específicas: ManimColor.from_hex(hex_str="...")

POSICIONAMENTO:
- Use constantes: UP, DOWN, LEFT, RIGHT, ORIGIN, UL, UR, DL, DR
- Métodos: .to_edge(), .to_corner(), .shift(), .move_to(), .next_to()
```

### Diferenças Manim CE vs ManimGL

| Feature | Manim CE (Use) | ManimGL (Evite) |
|---------|----------------|-----------------|
| Import | `from manim import *` | `from manimlib import *` |
| CLI | `manim render` | `manimgl` |
| Axes | `x_range=[min, max, step]` | `x_min, x_max, x_step` |
| hex param | `hex_str=` | `hex=` |
| section | `section_type=` | `type=` |

### Estratégia de few-shot examples

**Quantidade ótima**: 2-5 exemplos
- Muito poucos (0-1): Modelo pode não entender padrões
- Muitos (6+): Pode degradar performance
- Ideal: 3 exemplos cobrindo diferentes níveis de complexidade

### Comparação GPT-4o-mini vs GPT-4o

| Aspecto | GPT-4o-mini | GPT-4o |
|---------|-------------|--------|
| Contexto | 128K tokens | 128K tokens |
| Output máximo | 16K tokens | 16K tokens |
| Custo (input) | $0.15/1M tokens | $2.50/1M tokens |
| Custo (output) | $0.60/1M tokens | $10.00/1M tokens |
| Latência | Menor | Maior |
| Código complexo | Bom | Excelente |

#### Quando usar cada modelo

**GPT-4o-mini para:**
- Animações simples a moderadas
- Manipulações básicas de formas
- Visualizações matemáticas padrão
- Alto volume de geração
- Iteração e prototipagem

**GPT-4o para:**
- Animações multi-cena complexas
- Simulações físicas avançadas
- Visualizações de algoritmos novos
- Cenas 3D com câmera complexa
- Quando GPT-4o-mini falha após retries

### Parâmetros recomendados

```python
temperature = 0.0-0.3  # Menor é melhor para código
top_p = 0.9-0.95
max_tokens = 4000-8000  # Ajustar conforme complexidade
```

### Erros comuns de LLMs com Manim

```python
# ❌ ERRADO - Import ManimGL
from manimlib import *

# ✓ CORRETO - Manim CE
from manim import *

# ❌ ERRADO - Missing raw string
tex = MathTex("\\frac{1}{2}")

# ✓ CORRETO - Raw string
tex = MathTex(r"\frac{1}{2}")

# ❌ ERRADO - Sintaxe antiga de Axes
axes = Axes(x_min=-3, x_max=3)

# ✓ CORRETO - Manim CE
axes = Axes(x_range=[-3, 3, 1])

# ❌ ERRADO - Parâmetro antigo
ManimColor.from_hex(hex="#FF0000")

# ✓ CORRETO (0.19.0+)
ManimColor.from_hex(hex_str="#FF0000")

# ❌ ERRADO - Objetos sobrepostos
text1 = Text("Hello")
text2 = Text("World")
self.add(text1, text2)

# ✓ CORRETO - Posicionamento explícito
text1 = Text("Hello").shift(UP)
text2 = Text("World").shift(DOWN)
self.add(text1, text2)
```

### Templates de prompt por tipo

#### Explicações matemáticas
```
Crie uma animação Manim CE explicando [CONCEITO].

Requisitos:
- Comece com a fórmula/equação principal usando MathTex
- Decomponha cada componente com destaques visuais
- Mostre derivação ou transformação passo a passo
- Use cores para distinguir partes diferentes
- Inclua labels e anotações
- Termine com resultado final proeminente
```

#### Visualizações de algoritmos
```
Crie uma animação Manim CE visualizando o algoritmo [ALGORITMO].

Requisitos:
- Mostre estrutura de dados claramente
- Destaque elementos sendo comparados/trocados
- Exiba informação de estado atual (índices, valores)
- Use cores distintas para estados diferentes
- Inclua contador de passos ou iteração
- Mostre resultado final processado
```

### Validação e correção de erros

**Checklist pré-render:**
1. Verificar `from manim import *`
2. Confirmar herança correta de `Scene`
3. Verificar método `def construct(self):`
4. Checar sintaxe LaTeX (raw strings, chaves balanceadas)
5. Verificar posicionamento de objetos
6. Confirmar sequências `play()` e `wait()`

**Prompt de correção iterativa:**
```
O seguinte código Manim produziu erro:

```python
[CÓDIGO]
```

Mensagem de erro:
[ERRO]

Corrija o código focando em:
1. Import statements corretos para Manim CE
2. Sintaxe LaTeX correta (raw strings, chaves balanceadas)
3. Chamadas de método válidas para versão atual
4. Nomes de parâmetros corretos

Forneça apenas o código corrigido.
```

### Projetos existentes de LLM + Manim

- **Generative Manim** (github.com/marcelo-earth/generative-manim) - GPT-4o powered, 709+ stars
- **manim-generator** (github.com/makefinks/manim-generator) - Feedback loop code-writer/reviewer
- **Manimator** (arxiv.org/abs/2507.14306) - Pipeline acadêmico de duas etapas
- **Bespoke-Manim** (Hugging Face) - 1,000 scripts de animação matemática

---

## 10. Exemplos de código por categoria

### Transformação de equações

```python
from manim import *

class EquationDerivation(Scene):
    def construct(self):
        eq1 = MathTex("{{x}}^2", "+", "{{y}}^2", "=", "{{z}}^2")
        eq2 = MathTex("{{a}}^2", "+", "{{b}}^2", "=", "{{c}}^2")
        eq3 = MathTex("{{a}}^2", "=", "{{c}}^2", "-", "{{b}}^2")
        
        self.add(eq1)
        self.wait(0.5)
        self.play(TransformMatchingTex(eq1, eq2))
        self.wait(0.5)
        self.play(TransformMatchingTex(eq2, eq3))
        self.wait()
```

### Integral de Riemann

```python
from manim import *

class RiemannSum(Scene):
    def construct(self):
        ax = Axes(x_range=[0, 5], y_range=[0, 6], tips=False)
        curve = ax.plot(lambda x: 4*x - x**2, x_range=[0, 4], color=BLUE_C)
        
        # Retângulos de Riemann
        area = ax.get_riemann_rectangles(
            curve, x_range=[0.3, 3.7], dx=0.3,
            color=BLUE, fill_opacity=0.5
        )
        
        self.play(Create(ax))
        self.play(Create(curve))
        self.play(Create(area))
        self.wait()
```

### Cena 3D com rotação de câmera

```python
from manim import *

class ThreeDRotation(ThreeDScene):
    def construct(self):
        axes = ThreeDAxes()
        esfera = Sphere(radius=1, resolution=(20, 20))
        esfera.set_color(BLUE)
        
        self.set_camera_orientation(phi=75*DEGREES, theta=30*DEGREES)
        self.play(Create(axes), Create(esfera))
        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(5)
        self.stop_ambient_camera_rotation()
        self.move_camera(phi=45*DEGREES, theta=-45*DEGREES)
        self.wait()
```

### ValueTracker dinâmico

```python
from manim import *

class DynamicGraph(Scene):
    def construct(self):
        ax = Axes(x_range=[0, 10], y_range=[0, 100, 10])
        labels = ax.get_axis_labels(x_label="x", y_label="f(x)")
        
        tracker = ValueTracker(0)
        
        def func(x):
            return 2 * (x - 5) ** 2
        
        graph = ax.plot(func, color=MAROON)
        dot = always_redraw(
            lambda: Dot(ax.c2p(tracker.get_value(), func(tracker.get_value())))
        )
        
        self.add(ax, labels, graph, dot)
        self.play(tracker.animate.set_value(5), run_time=3)
        self.play(tracker.animate.set_value(10), run_time=3)
        self.wait()
```

### MovingCameraScene

```python
from manim import *

class CameraFollow(MovingCameraScene):
    def construct(self):
        self.camera.frame.save_state()
        
        ax = Axes(x_range=[-1, 10], y_range=[-1, 10])
        graph = ax.plot(lambda x: np.sin(x), color=WHITE, x_range=[0, 3*PI])
        
        dot_start = Dot(ax.i2gp(graph.t_min, graph))
        dot_end = Dot(ax.i2gp(graph.t_max, graph))
        
        self.add(ax, graph, dot_start, dot_end)
        self.play(self.camera.frame.animate.scale(0.5).move_to(dot_start))
        self.wait(0.5)
        self.play(self.camera.frame.animate.move_to(dot_end), run_time=3)
        self.wait(0.5)
        self.play(Restore(self.camera.frame))
        self.wait()
```

### Visualização de grafo

```python
from manim import *

class GraphVisualization(Scene):
    def construct(self):
        vertices = [1, 2, 3, 4, 5, 6, 7, 8]
        edges = [(1, 7), (1, 8), (2, 3), (2, 4), (2, 5), (2, 8), (3, 4)]
        
        g = Graph(vertices, edges, layout="spring")
        
        self.play(Create(g))
        self.wait(0.5)
        self.play(
            g[1].animate.move_to([1, 1, 0]),
            g[2].animate.move_to([-1, 1, 0])
        )
        self.wait()
```

### Animação de texto

```python
from manim import *

class TextAnimation(Scene):
    def construct(self):
        title = Text("Manim CE 0.19.0", font_size=72)
        subtitle = Text("Animações Matemáticas", font_size=36)
        equation = MathTex(r"e^{i\pi} + 1 = 0")
        
        VGroup(title, subtitle, equation).arrange(DOWN, buff=0.5)
        
        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=UP))
        self.play(Write(equation))
        self.wait()
        
        self.play(Indicate(equation))
        self.wait()
```

---

## 11. Limitações e workarounds

### Limitações técnicas

| Limitação | Descrição | Workaround |
|-----------|-----------|------------|
| Sem renderização real-time | Vídeos devem ser totalmente renderizados | Use `-ql` para desenvolvimento |
| Interatividade limitada | Outputs são arquivos de vídeo | Considere Motion Canvas para interatividade |
| Performance com muitos objetos | Renderização fica lenta | Agrupe com VGroup, remova objetos não usados |
| Constraints de memória | Cenas complexas podem exceder RAM | Quebre em múltiplas cenas |
| Tempo de render | Cenas 3D complexas demoram | Use `--renderer=opengl` para 3D |

### Limitações visuais

| Limitação | Descrição | Alternativa |
|-----------|-----------|-------------|
| Sem renderização fotorrealista | Projetado para gráficos vetoriais | Use Blender para raytracing |
| Iluminação 3D limitada | Modelo de luz básico, sem sombras | Blender para lighting avançado |
| Sem engine de física | Física deve ser codificada manualmente | manim-physics plugin ou Blender |
| Sistema de partículas limitado | Sem partículas nativas | Implementar manualmente |

### Workarounds de performance

```python
# 1. Quebrar cenas em partes
class Part1(Scene):
    def construct(self):
        # Primeira metade
        pass

class Part2(Scene):
    def construct(self):
        # Segunda metade
        pass

# 2. Usar qualidade baixa no desenvolvimento
# manim -pql scene.py MinhaScene

# 3. Desabilitar cache para problemas com TracedPath
# manim --disable_caching scene.py MinhaScene

# 4. Renderizar animações específicas
# manim -n 5,10 scene.py MinhaScene

# 5. Usar Text ao invés de Tex quando possível (mais rápido)
Text("Hello World")  # Rápido
Tex("Hello World")   # Requer LaTeX, mais lento
```

### Gerenciamento de memória

```python
# Remover objetos quando não necessários
self.play(FadeOut(old_object))
self.remove(old_object)

# Usar always_redraw com cuidado
# Cria novo objeto a cada frame - usar esparçamente
number = always_redraw(lambda: DecimalNumber(tracker.get_value()))

# Melhor para objetos complexos: usar add_updater
number = DecimalNumber(0)
number.add_updater(lambda m: m.set_value(tracker.get_value()))
```

### Quando usar alternativas

| Necessidade | Ferramenta |
|-------------|------------|
| Vídeos de educação matemática | **Manim** ✓ |
| Preview real-time | Motion Canvas |
| Integração React | Remotion |
| 3D fotorrealista | Blender |
| App web interativo | p5.js / Three.js |
| Protótipo rápido | p5.js |
| Física complexa | Blender |
| Equações LaTeX | **Manim** ✓ |

---

## 12. Recursos da comunidade

### Canais oficiais

- **Discord**: Hub principal da comunidade (discord.gg/manim)
- **Reddit**: r/manim - compartilhamento de projetos e perguntas
- **Stack Overflow**: Tag `manim` para Q&A
- **GitHub Discussions**: Para propostas e perguntas técnicas

### Repositórios essenciais

| Repositório | Descrição | Stars |
|-------------|-----------|-------|
| ManimCommunity/manim | Repositório principal | 31.9k |
| 3b1b/manim | ManimGL original | 82.5k |
| 3b1b/videos | Código de todos os vídeos 3B1B | — |
| ManimCommunity/awesome-manim | Lista de criadores usando Manim | — |
| helblazer811/ManimML | Visualizações de ML | — |
| jeertmans/manim-slides | Apresentações com Manim | — |

### Plugins populares

| Plugin | Propósito | Install |
|--------|-----------|---------|
| manim-voiceover | Narração em Python | `pip install manim-voiceover` |
| manim-slides | Apresentações PowerPoint-like | `pip install manim-slides` |
| ManimML | Visualizações de ML | `pip install manim-ml` |
| manim-physics | Simulações físicas | — |
| Chanim | Química | — |

### Playground interativo

- **https://try.manim.community** - Jupyter notebook online, sem instalação

### Tutoriais recomendados

- Quickstart oficial: docs.manim.community/tutorials/quickstart.html
- Building Blocks: docs.manim.community/tutorials/building_blocks.html
- manimclass.com - Tutoriais step-by-step gratuitos

---

## 13. Referência rápida e cheatsheets

### Comandos CLI essenciais

```bash
# Render com preview
manim -pql scene.py MinhaScene

# Alta qualidade final
manim -qh scene.py MinhaScene

# GIF output
manim --format=gif -ql scene.py MinhaScene

# Background transparente
manim -t scene.py MinhaScene

# Verificar instalação
manim checkhealth

# Inicializar projeto
manim init
```

### Estrutura básica de código

```python
from manim import *

class MinhaScene(Scene):
    def construct(self):
        # Criar objetos
        obj = Circle()
        
        # Animar
        self.play(Create(obj))
        self.wait()
```

### Constantes de buffer

```python
SMALL_BUFF = 0.1
MED_SMALL_BUFF = 0.25
MED_LARGE_BUFF = 0.5
LARGE_BUFF = 1

# Uso
obj.next_to(outro, RIGHT, buff=MED_SMALL_BUFF)
```

### Constantes matemáticas

```python
PI = np.pi
TAU = 2 * np.pi
DEGREES = PI / 180

# Uso
self.play(Rotate(obj, PI/2))
self.play(Rotate(obj, 90*DEGREES))
```

### Dimensões do frame

```python
config.frame_height = 8.0      # Altura lógica
config.frame_width = 14.22...  # Largura lógica (16:9)
config.pixel_height = 1080
config.pixel_width = 1920
```

### Animações mais usadas

```python
# Criação
self.play(Create(obj))
self.play(Write(texto))
self.play(FadeIn(obj))
self.play(GrowFromCenter(obj))

# Transformação
self.play(Transform(a, b))
self.play(ReplacementTransform(a, b))
self.play(TransformMatchingTex(eq1, eq2))

# Movimento
self.play(obj.animate.shift(UP * 2))
self.play(obj.animate.move_to(ORIGIN))
self.play(obj.animate.scale(2))
self.play(Rotate(obj, PI/2))

# Indicação
self.play(Indicate(obj))
self.play(Circumscribe(obj))
self.play(Flash(obj.get_center()))

# Saída
self.play(FadeOut(obj))
self.play(Uncreate(obj))
```

### Configuração programática

```python
from manim import config

# Qualidade
config.pixel_width = 1920
config.pixel_height = 1080
config.frame_rate = 60

# Background
config.background_color = WHITE

# Transparência
config.transparent = True
config.format = "webm"

# Cache
config.disable_caching = True
```

### Checklist pré-geração para LLMs

1. ✅ Import: `from manim import *`
2. ✅ Herança: `class X(Scene):`
3. ✅ Método: `def construct(self):`
4. ✅ Raw strings para LaTeX: `MathTex(r"...")`
5. ✅ Posicionamento explícito de objetos
6. ✅ Chamadas `self.wait()` para ritmo
7. ✅ Parâmetros keyword para SurroundingRectangle
8. ✅ `hex_str=` ao invés de `hex=` para cores

---

## Conclusão

Este guia cobre o ecossistema completo do **Manim Community Edition 0.19.0** e sua integração com **GPT-4o-mini** para geração automatizada de código. As principais conclusões são:

A versão 0.19.0 simplifica drasticamente a instalação ao substituir ffmpeg por PyAV, tornando o Manim mais acessível. Para geração de código via LLM, GPT-4o-mini oferece excelente custo-benefício para animações simples a moderadas, enquanto GPT-4o é preferível para cenários complexos. O segredo está em system prompts bem estruturados que especificam claramente a versão do Manim CE, evitam confusão com ManimGL, e incluem few-shot examples de qualidade.

Os erros mais comuns podem ser prevenidos enfatizando raw strings para LaTeX, usando `x_range` ao invés de `x_min/x_max`, e especificando posicionamento explícito de objetos. Com estas práticas, a combinação Manim + LLM permite criar conteúdo educacional animado de alta qualidade de forma eficiente e escalável.
```
