from typing import Callable
from definitions import GameState, ObjectId, ItemId, LocationId, Condition


ConditionFactory = Callable[[dict], Condition]
CONDITIONS: dict[str, ConditionFactory] = {}


def register_condition(name: str):
    def decorator(fn: ConditionFactory):
        CONDITIONS[name] = fn
        return fn
    return decorator


@register_condition("has_item")
def has_item(data: dict) -> Condition:
    item = ItemId(data["item"])
    def _cond(state: GameState) -> bool:
        return state.inventory.has(item)
    return _cond

@register_condition("container_locked")
def container_locked(data: dict) -> Condition:
    cid = ObjectId(data["container"])

    def _cond(state: GameState) -> bool:
        try:
            return state.objects[cid].flags["locked"]
        except ValueError:
            return False
    return _cond

@register_condition("in_location")
def entity_in_location(data: dict) -> Condition:
    lid = LocationId(data["location"])
    def _cond(state: GameState) -> bool:
        return state.current_location == lid
    return _cond