from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, auto, unique

from damsel.model.content import Choice
from damsel.model.types import ActionId, ItemId, ObjectId


@unique
class NavKind(StrEnum):
    """Виды навигационных действий (переключение UI-контекста)."""

    BACK = auto()
    OPEN_INVENTORY = auto()
    FOCUS_ITEM = auto()
    FOCUS_OBJECT = auto()


@dataclass(frozen=True)
class GameAction:
    """Игровое действие: обёртка над доменным Choice (эффекты, условия, результат)."""

    choice: Choice

    @property
    def id(self) -> ActionId:
        return ActionId(self.choice.id)

    @property
    def text(self) -> str:
        return self.choice.text


@dataclass(frozen=True)
class NavAction:
    """Навигационное действие: меняет UI-контекст, не затрагивает состояние мира."""

    id: ActionId
    text: str
    kind: NavKind
    target: ItemId | ObjectId | None = None


Action = GameAction | NavAction
