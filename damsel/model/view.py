"""ViewModel — структурированное представление игры для фронтендов.

Фронтенд (CLI, веб, телеграм-бот) получает GameView и сам решает, как его
отрисовать. Русских строк и presentation-логики здесь нет: статусы объектов —
enum, тексты кнопок приходят из провайдеров действий.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, auto, unique

from damsel.model.content import GameContent, ObjectKind, UIContext
from damsel.model.state import GameState, ObjectState
from damsel.model.types import ActionId, ItemId, LocationId, ObjectId


@unique
class ObjectStatus(StrEnum):
    LOCKED = auto()
    CLOSED = auto()
    OPEN = auto()
    ON = auto()
    OFF = auto()


@unique
class ActionKind(StrEnum):
    GAME = auto()
    NAV = auto()


@dataclass(frozen=True)
class ItemView:
    id: ItemId
    name: str


@dataclass(frozen=True)
class ObjectView:
    id: ObjectId
    kind: ObjectKind
    name: str
    description: str | None = None  # показывается при verbose либо для дверей/выключателей
    status: ObjectStatus | None = None  # None — у объекта нет осмысленного статуса
    items_inside: list[ItemView] = field(default_factory=list)


@dataclass(frozen=True)
class ActionView:
    id: ActionId  # непрозрачен: фронтенд возвращает его в dispatch() как есть
    text: str
    kind: ActionKind


@dataclass(frozen=True)
class GameView:
    context: UIContext
    title: str | None  # None — фронтенд не показывает шапку локации
    description: str | None  # заполняется только при первом посещении (verbose)
    objects: list[ObjectView] = field(default_factory=list)
    floor_items: list[ItemView] = field(default_factory=list)
    inventory: list[ItemView] = field(default_factory=list)
    message: str | None = None  # результат прошлого действия, one-shot
    actions: list[ActionView] = field(default_factory=list)
    finished: bool = False


def object_status(
    kind: ObjectKind, defn_can_open: bool, st: ObjectState
) -> ObjectStatus | None:
    match kind:
        case ObjectKind.CONTAINER:
            if st.is_locked:
                return ObjectStatus.LOCKED
            if not defn_can_open:
                return None
            return ObjectStatus.OPEN if st.is_open else ObjectStatus.CLOSED
        case ObjectKind.DOOR:
            return ObjectStatus.OPEN if st.is_open else ObjectStatus.CLOSED
        case ObjectKind.SWITCH:
            return ObjectStatus.ON if st.is_on else ObjectStatus.OFF


def item_view(content: GameContent, iid: ItemId) -> ItemView:
    return ItemView(id=iid, name=content.items[iid].name)


def build_object_views(
    content: GameContent,
    state: GameState,
    location_id: LocationId,
    verbose: bool,
) -> list[ObjectView]:
    views: list[ObjectView] = []
    for oid in content.locations[location_id].objects:
        defn = content.furniture[oid]
        st = state.objects[oid]
        show_description = verbose or defn.kind is not ObjectKind.CONTAINER
        items_inside: list[ItemView] = []
        if defn.is_container and st.is_open and not st.is_locked:
            items_inside = [item_view(content, iid) for iid in st.items]
        views.append(
            ObjectView(
                id=oid,
                kind=defn.kind,
                name=defn.name,
                description=defn.description if show_description else None,
                status=object_status(defn.kind, defn.can_open, st),
                items_inside=items_inside,
            )
        )
    return views
