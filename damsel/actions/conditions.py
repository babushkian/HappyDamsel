from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
from damsel.model.types import ItemId, ObjectId, LocationId, Condition, INVENTORY_LOCATION_ID

if TYPE_CHECKING:
    from damsel.model import GameState, GameContent

ConditionFactory = Callable[[dict[str, Any]], Condition]
CONDITIONS: dict[str, ConditionFactory] = {}


def register_condition(name: str) -> Callable[[ConditionFactory], ConditionFactory]:
    def decorator(fn: ConditionFactory) -> ConditionFactory:
        CONDITIONS[name] = fn
        return fn

    return decorator


@register_condition("has_item")
def has_item(data: dict[str, Any]) -> Condition:
    item = ItemId(data["item"])

    def _cond(state: GameState, content: GameContent) -> bool:
        return item in state.locations_items[INVENTORY_LOCATION_ID]

    return _cond


@register_condition("container_locked")
def container_locked(data: dict[str, Any]) -> Condition:
    cid = ObjectId(data["container"])

    def _cond(state: GameState, content: GameContent) -> bool:
        obj = state.objects.get(cid)
        return obj.is_locked if obj is not None else False

    return _cond


@register_condition("in_location")
def in_location(data: dict[str, Any]) -> Condition:
    lid = LocationId(data["location"])

    def _cond(state: GameState, content: GameContent) -> bool:
        return state.current_location == lid

    return _cond


@register_condition("object_is_open")
def object_is_open(data: dict[str, Any]) -> Condition:
    oid = ObjectId(data["object"])

    def _cond(state: GameState, content: GameContent) -> bool:
        o = state.objects.get(oid)
        if o is None:
            raise ValueError(f"Object {oid} does not exist")
        odef = content.furniture.get(oid)
        if odef is None or not odef.can_open:
            raise ValueError(f"Object {oid} is not openable")
        return o.is_open

    return _cond


@register_condition("object_is_closed")
def object_is_closed(data: dict[str, Any]) -> Condition:
    oid = ObjectId(data["object"])

    def _cond(state: GameState, content: GameContent) -> bool:
        o = state.objects.get(oid)
        if o is None:
            raise ValueError(f"Object {oid} does not exist")
        odef = content.furniture.get(oid)
        if odef is None or not odef.can_open:
            raise ValueError(f"Object {oid} is not openable")
        return not o.is_open

    return _cond


@register_condition("object_is_on")
def object_is_on(data: dict[str, Any]) -> Condition:
    oid = ObjectId(data["object"])

    def _cond(state: GameState, content: GameContent) -> bool:
        o = state.objects.get(oid)
        if o is None:
            raise ValueError(f"Object {oid} does not exist")
        odef = content.furniture.get(oid)
        if odef is None or not odef.turnable:
            raise ValueError(f"Object {oid} is not turnable")
        return o.is_on

    return _cond


@register_condition("object_is_off")
def object_is_off(data: dict[str, Any]) -> Condition:
    oid = ObjectId(data["object"])

    def _cond(state: GameState, content: GameContent) -> bool:
        o = state.objects.get(oid)
        if o is None:
            raise ValueError(f"Object {oid} does not exist")
        odef = content.furniture.get(oid)
        if odef is None or not odef.turnable:
            raise ValueError(f"Object {oid} is not turnable")
        return not o.is_on

    return _cond


@register_condition("location_lit")
def location_lit(data: dict[str, Any]) -> Condition:
    """Освещена ли локация. Без параметра — текущая локация игрока."""
    from damsel.model.display import is_location_lit

    lid = LocationId(data["location"]) if "location" in data else None

    def _cond(state: GameState, content: GameContent) -> bool:
        target = lid if lid is not None else state.current_location
        return is_location_lit(content, state, target)

    return _cond


@register_condition("flag_set")
def flag_set(data: dict[str, Any]) -> Condition:
    flag = data["flag"]

    def _cond(state: GameState, content: GameContent) -> bool:
        return state.flags.get(flag, False)

    return _cond


@register_condition("flag_not_set")
def flag_not_set(data: dict[str, Any]) -> Condition:
    flag = data["flag"]

    def _cond(state: GameState, content: GameContent) -> bool:
        return not state.flags.get(flag, False)

    return _cond


@register_condition("never")
def never(data: dict[str, Any]) -> Condition:
    """Всегда ложно. Например, для lit_when вечно тёмной локации."""

    def _cond(state: GameState, content: GameContent) -> bool:
        return False

    return _cond
