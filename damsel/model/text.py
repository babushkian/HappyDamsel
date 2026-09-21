"""Условные тексты: строка ИЛИ список вариантов с условиями.

Описания локаций, объектов и предметов могут зависеть от состояния мира
(свет, флаги, открытые двери). Текст не хранит состояние — он вычисляется
в момент показа через те же Condition, что и доступность выборов.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from damsel.model.types import Condition

if TYPE_CHECKING:
    from damsel.model.content import GameContent
    from damsel.model.state import GameState


@dataclass(frozen=True)
class ConditionalText:
    """Первый подходящий по условиям вариант побеждает; иначе default."""

    variants: list[tuple[list[Condition], str]] = field(default_factory=list)
    default: str | None = None

    def resolve(self, state: "GameState", content: "GameContent") -> str | None:
        for when, text in self.variants:
            if all(cond(state, content) for cond in when):
                return text
        return self.default


Text = str | ConditionalText


def resolve_text(text: Text | None, state: "GameState", content: "GameContent") -> str | None:
    """str проходит как есть, ConditionalText резолвится от состояния, None -> None."""
    if text is None:
        return None
    if isinstance(text, ConditionalText):
        return text.resolve(state, content)
    return text
