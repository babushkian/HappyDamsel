from typing import TYPE_CHECKING, Callable

from damsel.model.content import ObjectKind
from damsel.model.types import (
    INVENTORY_LOCATION_ID,
    Effect,
    ItemId,
    LocationId,
    ObjectId,
)

if TYPE_CHECKING:
    from damsel.model.content import GameContent
    from damsel.model.state import GameState

EffectFactory = Callable[[dict], Effect]
EFFECTS: dict[str, EffectFactory] = {}


def register_effect(name: str):
    def decorator(fn: EffectFactory):
        EFFECTS[name] = fn
        return fn

    return decorator


@register_effect("consume_item")
def consume_item(data: dict) -> Effect:
    item = ItemId(data["item"])

    def _effect(state: "GameState", content: "GameContent") -> None:
        inv = state.locations_items[INVENTORY_LOCATION_ID]
        if item in inv:
            inv.remove(item)

    return _effect


@register_effect("unlock_container")
def unlock_container(data: dict) -> Effect:
    cid = ObjectId(data["container"])

    def _effect(state: "GameState", content: "GameContent") -> None:
        c = state.objects[cid]
        c.is_locked = False
        c.is_open = True

    return _effect


@register_effect("reveal_contents")
def reveal_contents(data: dict) -> Effect:
    cid = ObjectId(data["container"])

    def _effect(state: "GameState", content: "GameContent") -> None:
        c = state.objects[cid]
        for item in c.items:
            state.locations_items[INVENTORY_LOCATION_ID].append(item)
        c.items.clear()

    return _effect


@register_effect("get_item")
def get_item(data: dict) -> Effect:
    iid = ItemId(data["item"])

    def _effect(state: "GameState", content: "GameContent") -> None:
        loc_items = state.locations_items[state.current_location]
        if iid in loc_items:
            loc_items.remove(iid)
        state.locations_items[INVENTORY_LOCATION_ID].append(iid)

    return _effect


@register_effect("drop_item")
def drop_item(data: dict) -> Effect:
    iid = ItemId(data["item"])

    def _effect(state: "GameState", content: "GameContent") -> None:
        inv = state.locations_items[INVENTORY_LOCATION_ID]
        if iid in inv:
            inv.remove(iid)
        state.locations_items[state.current_location].append(iid)

    return _effect


@register_effect("move_to")
def move_to(data: dict) -> Effect:
    lid = LocationId(data["location"])

    def _effect(state: "GameState", content: "GameContent") -> None:
        if lid not in content.locations:
            raise ValueError(f"Location {lid} does not exist")
        state.current_location = lid

    return _effect


@register_effect("open_object")
def open_object(data: dict) -> Effect:
    oid = ObjectId(data["object"])

    def _effect(state: "GameState", content: "GameContent") -> None:
        odef = content.furniture.get(oid)
        if odef is None or not odef.can_open:
            raise ValueError(f"Object {oid} is not openable")
        state.objects[oid].is_open = True
        if odef.kind is ObjectKind.DOOR and odef.link_to:
            state.objects[odef.link_to].is_open = True

    return _effect


@register_effect("close_object")
def close_object(data: dict) -> Effect:
    oid = ObjectId(data["object"])

    def _effect(state: "GameState", content: "GameContent") -> None:
        odef = content.furniture[oid]
        if not odef.can_open:
            raise ValueError(f"Object {oid} is not openable")
        state.objects[oid].is_open = False
        if odef.kind is ObjectKind.DOOR and odef.link_to:
            state.objects[odef.link_to].is_open = False

    return _effect
