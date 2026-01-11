from typing import Callable
from definitions import GameState, ObjectId, ItemId, LocationId,  Effect


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

    def _effect(state: GameState):
        state.inventory.remove(item)

    return _effect

@register_effect("unlock_container")
def make_unlock_and_open(data: dict) -> Effect:
    cid = ObjectId(data["container"])

    def _effect(state: GameState) -> None:
        c = state.get_container(cid)
        c.locked = False
        c.open = True
    return _effect

@register_effect("reveal_contents")
def make_reveal_contents(data: dict) -> Effect:
    cid = ObjectId(data["container"])
    def _effect(state: GameState) -> None:
        c = state.get_container(cid)
        for item in c.contents:
            state.inventory.add(item)
        c.contents.clear()
    return _effect

@register_effect("get_item")
def make_get_item(data: dict) -> Effect:
    iid = ItemId(data["item"])

    def _effect(state: GameState) -> None:
        state.location().items.remove(iid)
        state.inventory.add(iid)
    return _effect


@register_effect("move_to")
def make_move_to(data: dict) -> Effect:
    lid = LocationId(data["location"])
    def _effect(state: GameState) -> None:
        state.move_to(lid)
    return _effect

