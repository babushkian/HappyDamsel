from typing import Callable
from definitions import GameState, ObjectId, ItemId, LocationId, Condition, Container

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
    container: Container,
    item: ItemId | None = None,
) -> Callable[[GameState], str]:
    def render(_: GameState) -> str:
        if item:
            return (
                f"Вы открыли {container.name} с помощью {item.value}."
            )
        return f"Вы открыли {container.name}."
    return render