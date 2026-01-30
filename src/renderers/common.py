

TEMPLATES = {
    "generic_unlock": "Ты открыл {object} с помощью {item}.",
    "generic_pickup": "Ты подобрал {item}.",
    "generic_drop": "Ты выбросил {item}.",
    "generic_open": "Ты открыл {object}.",
    "generic_close": "Ты закрыл {object}."
}

def render_template(result: "Result", content: "GameContent"):
    if result.template not in TEMPLATES:
        raise ValueError(f"Не обнаружен шаблон для {result.template!r}")
    resolved = {}
    for key, value in result.params.items():
        if value in content.items:
            resolved[key] = content.items[value].name
        elif value in content.furniture:
            resolved[key] = content.furniture[value].name
        else:
            resolved[key] = value

    return TEMPLATES[result.template].format(**resolved)

