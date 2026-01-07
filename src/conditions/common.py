from typing import Callable
from definitions import GameState, ObjectId, ItemId, Condition


ConditionFactory = Callable[[GameState, dict], Condition]
CONDITIONS: dict[str, ConditionFactory] = {}


def register_condition(name: str):
    def decorator(fn: ConditionFactory):
        CONDITIONS[name] = fn
        return fn
    return decorator


@register_condition("has_item")
def has_item(state: GameState, data: dict) -> Condition:
    item = ItemId(data["item"])
    def _cond() -> bool:
        return state.inventory.has(item)
    return _cond

@register_condition("container_locked")
def container_locked(state: GameState, data: dict) -> Condition:
    cid = ObjectId(data["container"])

    def _cond() -> bool:
        try:
            return state.get_container(cid).locked
        except ValueError:
            return False
    return _cond

