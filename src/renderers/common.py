from typing import Callable
from definitions import GameState,  ItemDef, Condition, FurnitureDef

Renderer = Callable[[GameState], str]
RenderFactory = Callable[[dict], Condition]
RENDERERS: dict[str, RenderFactory] = {}


def register_renderer(name: str):
    def decorator(fn: RenderFactory):
        RENDERERS[name] = fn
        return fn
    return decorator

@register_renderer("open_container")
def open_container_template(
    furn: FurnitureDef,
    item: ItemDef | None = None,
) -> Callable[[GameState], str]:

    def render(_: GameState) -> str:
        if item:
            return (
                f"Вы открыли {furn.name} с помощью {item.name}."
            )
        return f"Вы открыли {furn.name}."
    return render