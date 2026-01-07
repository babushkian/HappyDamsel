from typing import Callable
from definitions import GameState, ObjectId, ItemId, Condition

Condition = Callable[[GameState], bool]
ConditionFactory = Callable[[dict], Condition]


Effect = Callable[[GameState], None]
EffectFactory = Callable[[dict], Effect]


ConditionFactory = Callable[[GameState, dict], Condition]
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
            return state.get_container(cid).locked
        except ValueError:
            return False
    return _cond

