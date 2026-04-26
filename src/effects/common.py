from typing import Callable
from definitions import GameState, ObjectId, ItemId, LocationId, Effect, INVENTORY_LOCATION_ID

EffectFactory = Callable[[dict], Effect]
EFFECTS: dict[str, EffectFactory] = {}


def register_effect(name: str):
    def decorator(fn: EffectFactory):
        EFFECTS[name] = fn
        return fn
    return decorator


@register_effect("consume_item")
def make_consume_item(data: dict):
    item = ItemId(data["item"])

    def _effect(state: GameState, content: "GameContent"):
        inv_items = state.locations_items[INVENTORY_LOCATION_ID]
        if item in inv_items:
            inv_items.remove(item)

    return _effect

@register_effect("unlock_container")
def make_unlock_and_open(data: dict) -> Effect:
    cid = ObjectId(data["container"])

    def _effect(state: GameState, content: "GameContent") -> None:
        c = state.objects[cid]
        c.flags["locked"] = False
        c.flags["open"] = True
    return _effect


@register_effect("reveal_contents")
def make_reveal_contents(data: dict) -> Effect:
    cid = ObjectId(data["container"])
    def _effect(state: GameState, content: "GameContent") -> None:
        c = state.objects[cid]
        for item in c.items:
            state.locations_items[INVENTORY_LOCATION_ID].append(item)
        c.items.clear()
    return _effect


@register_effect("get_item")
def make_get_item(data: dict) -> Effect:
    iid = ItemId(data["item"])

    def _effect(state: GameState, content: "GameContent") -> None:
        loc_items = state.locations_items[state.current_location]
        if iid in loc_items:
            loc_items.remove(iid)
        state.locations_items[INVENTORY_LOCATION_ID].append(iid)
    return _effect


@register_effect("drop_item")
def make_drop_item(data: dict) -> Effect:
    iid = ItemId(data["item"])
    def _effect(state: GameState, content: "GameContent") -> None:
        inv_items = state.locations_items[INVENTORY_LOCATION_ID]
        if iid in inv_items:
            inv_items.remove(iid)
        state.locations_items[state.current_location].append(iid)

    return _effect


@register_effect("move_to")
def make_move_to(data: dict) -> Effect:
    lid = LocationId(data["location"])
    def _effect(state: GameState, content: "GameContent") -> None:
        if lid not in content.locations:
            raise ValueError(f"Location {lid} does not exist")
        state.current_location = lid
    return _effect


@register_effect("open_object")
def make_open_object(data: dict) -> Effect:
    oid = ObjectId(data["object"])
    def _effect(state: GameState, content: "GameContent") -> None:
        odef = content.furniture.get(oid)
        if not odef.can_open:
            raise ValueError(f"Object {oid} is not openable")
        o = state.objects[oid]
        o.flags["open"] = True
        if odef.kind == "door":
            linked_obj = state.objects[odef.link_to]
            linked_obj.flags["open"] = True
    return _effect

@register_effect("close_object")
def make_close_object(data: dict) -> Effect:
    oid = ObjectId(data["object"])
    def _effect(state: GameState, content: "GameContent") -> None:
        odef = content.furniture.get(oid)
        if not odef.can_open:
            raise ValueError(f"Object {oid} is not openable")
        o = state.objects[oid]
        o.flags["open"] = False
        if odef.kind == "door":
            linked_obj = state.objects[odef.link_to]
            linked_obj.flags["open"] = True
    return _effect