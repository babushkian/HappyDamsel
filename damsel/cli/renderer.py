"""Рендер GameView в текст для терминала.

Единственное место, где живут русские строки статусов и особенности
терминального формата. Чистая функция: GameView -> str, без состояния.
"""

from __future__ import annotations

from damsel.model.content import ObjectKind
from damsel.model.view import GameView, ObjectStatus, ObjectView

CONTAINER_STATUS: dict[ObjectStatus, str] = {
    ObjectStatus.LOCKED: "(заперто)",
    ObjectStatus.CLOSED: "(закрыто)",
    ObjectStatus.OPEN: "",
}
DOOR_STATUS: dict[ObjectStatus, str] = {
    ObjectStatus.OPEN: "(открыто)",
    ObjectStatus.CLOSED: "(закрыто)",
}
SWITCH_STATUS: dict[ObjectStatus, str] = {
    ObjectStatus.ON: "(включено)",
    ObjectStatus.OFF: "(выключено)",
}


def render_view(view: GameView) -> str:
    parts: list[str] = []
    if view.message:
        parts.append(f"{view.message}\n")
    if view.title is not None:
        parts.append(_render_location(view))
    parts.append(_render_actions(view))
    return "".join(parts)


def _render_location(view: GameView) -> str:
    assert view.title is not None
    lines = [view.title]
    if view.description:
        lines.append(view.description)
    for obj in view.objects:
        lines.append(_render_object(obj))
    if view.floor_items:
        names = ", ".join(i.name for i in view.floor_items)
        lines.append(f"Здесь находится: {names}")
    if view.inventory:
        names = ", ".join(i.name for i in view.inventory)
        lines.append(f"В инвентаре: {names}")
    return "".join(f"{line}\n" for line in lines) + "\n"


def _render_object(obj: ObjectView) -> str:
    """Одна строка описания объекта, без завершающего \\n (добавляет _render_location)."""
    match obj.kind:
        case ObjectKind.CONTAINER:
            # status None (напр. стеллаж) — без хвостового пробела;
            # OPEN даёт пустую строку статуса — пробел сохраняется (квирк старого вывода)
            suffix = f" {CONTAINER_STATUS[obj.status]}" if obj.status is not None else ""
            if obj.description is not None:
                return f"{obj.name}{suffix}. {obj.description}"
            return f"{obj.name}{suffix}"
        case ObjectKind.DOOR:
            status = DOOR_STATUS[obj.status] if obj.status is not None else ""
            return f"{obj.name}{status}. {obj.description or ''}"
        case ObjectKind.SWITCH:
            status = SWITCH_STATUS[obj.status] if obj.status is not None else ""
            return f"{obj.name}{status}. {obj.description or ''}"


def _render_actions(view: GameView) -> str:
    return "".join(f"{n}. {a.text}\n" for n, a in enumerate(view.actions, 1)) + "\n"
