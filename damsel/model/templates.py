from damsel.model.content import Result, GameContent
from damsel.model.types import ItemId, ObjectId

TEMPLATES = {
    "generic_unlock": "Ты открыл {object} с помощью {item}.",
    "generic_pickup": "Ты подобрал {item}.",
    "generic_drop": "Ты выбросил {item}.",
    "generic_open": "Ты открыл {object}.",
    "generic_close": "Ты закрыл {object}.",
}


def render_template(result: Result, content: GameContent) -> str:
    if result.template not in TEMPLATES:
        raise ValueError(f"Шаблон {result.template!r} не найден")
    resolved: dict[str, str] = {}
    for key, value in result.params.items():
        item = content.items.get(ItemId(value))
        furn = content.furniture.get(ObjectId(value))
        if item is not None:
            resolved[key] = item.name
        elif furn is not None:
            resolved[key] = furn.name
        else:
            resolved[key] = value
    return TEMPLATES[result.template].format(**resolved)
