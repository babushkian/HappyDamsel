from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from enum import StrEnum, auto, unique
from damsel.model.types import Condition, Effect, ItemId, LocationId, ObjectId

if TYPE_CHECKING:
    from damsel.model import GameContent, GameState

@unique
class UIContext(StrEnum):
    LOCATION = auto()
    INVENTORY = auto()
    OBJECT_FOCUS = auto()
    ITEM_FOCUS = auto()


@unique
class ObjectKind(StrEnum):
    """Виды фурнитуры. Значения совпадают со строками в data/objects/*.yaml."""

    CONTAINER = auto()
    DOOR = auto()
    SWITCH = auto()


@unique
class ChoiceScope(StrEnum):
    """В каком UI-контексте показывать статический выбор из YAML."""

    LOCATION = auto()
    ITEM_FOCUS = auto()
    OBJECT_FOCUS = auto()


@dataclass(frozen=True)
class ItemDef:
    id: ItemId
    name: str
    description: str
    consumable: bool


@dataclass(frozen=True)
class FurnitureDef:
    id: ObjectId
    kind: ObjectKind
    name: str
    description: str
    can_open: bool = False
    can_lock: bool = False
    is_container: bool = False
    is_transparent: bool = False
    turnable: bool = False
    link_to: ObjectId | None = None


@dataclass(frozen=True)
class LocationDef:
    id: LocationId
    name: str
    description: str
    objects: list[ObjectId]
    # TODO это очень спорное решение, так как список предметов в локации актуален только вначале игры
    #  потом предметы могут перемещаться
    #  если в программе имеются обращения к этому полю, это очень опасно
    items: list[ItemId]


@dataclass(frozen=True)
class Result:
    template: str
    params: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Choice:
    id: str
    text: str
    when: list[Condition] = field(default_factory=list)
    do: list[Effect] = field(default_factory=list)
    result_text: str | None = None
    result: Result | None = None
    scope: ChoiceScope = ChoiceScope.LOCATION
    is_ui: bool = False

    def is_available(self, state: GameState, content: GameContent) -> bool:
        return all(cond(state, content) for cond in self.when)

    def apply(self, state: GameState, content: GameContent) -> str:
        if not self.is_available(state, content):
            raise RuntimeError("Conditions not met")
        for effect in self.do:
            effect(state, content)
        if self.result_text is not None:
            return self.result_text
        if self.result is not None:
            from damsel.model.templates import render_template

            return render_template(self.result, content)
        return ""


@dataclass(frozen=True)
class GameContent:
    items: dict[ItemId, ItemDef]
    furniture: dict[ObjectId, FurnitureDef]
    locations: dict[LocationId, LocationDef]
    choices: dict[str, Choice]


@dataclass(frozen=True)
class RawContent:
    items: dict = field(default_factory=dict)
    locations: dict = field(default_factory=dict)
    objects: dict = field(default_factory=dict)
    choices: dict = field(default_factory=dict)
