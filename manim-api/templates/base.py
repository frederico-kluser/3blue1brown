"""Classe base para templates determinísticos de clipes Manim."""

from abc import ABC, abstractmethod
from typing import Any


class ClipTemplate(ABC):
    """Template determinístico de cena Manim.

    Subclasses devem definir ``name`` e implementar :meth:`render`,
    retornando uma tupla ``(scene_name, code)``. O ``code`` deve conter
    ``from manim import *`` e uma única classe herdando de :class:`Scene`,
    sem configurar cor de fundo (ela é injetada pelo renderizador).
    """

    name: str = ""
    description: str = ""

    @classmethod
    @abstractmethod
    def render(
        cls,
        width: int,
        height: int,
        background_color: str,
        fps: int,
        **kwargs: Any,
    ) -> tuple[str, str]:
        """Renderiza o template para os parâmetros dados.

        Returns
        -------
        tuple[str, str]
            Nome da cena e código-fonte Manim CE pronto para execução.
        """
        raise NotImplementedError
