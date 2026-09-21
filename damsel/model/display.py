"""Производные свойства отображения: освещённость, видимость, оверрайды имён.

Ничего не хранится в GameState — всё вычисляется из фактов мира:
- локация освещена, если выполнены все её условия lit_when;
- объект виден, если выполнены все его условия visible_when;
- содержимое контейнера видно, если виден сам контейнер и выполнены
  его условия contents_visible_when;
- имя/описание объекта могут переопределяться для конкретной локации
  (одна дверь на две локации называется с каждой стороны по-своему).

Эти предикаты обязаны использовать и view-слой, и провайдеры действий:
невидимый предмет нельзя не только показать, но и взять.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from damsel.model.text import Text, resolve_text
from damsel.model.types import LocationId, ObjectId

if TYPE_CHECKING:
    from damsel.model.content import GameContent, ObjectOverride
    from damsel.model.state import GameState


def is_location_lit(content: GameContent, state: GameState, lid: LocationId) -> bool:
    """Пустой lit_when означает «всегда светло»."""
    return all(c(state, content) for c in content.locations[lid].lit_when)


def is_object_visible(content: GameContent, state: GameState, oid: ObjectId) -> bool:
    return all(c(state, content) for c in content.furniture[oid].visible_when)


def are_contents_visible(content: GameContent, state: GameState, oid: ObjectId) -> bool:
    defn = content.furniture[oid]
    if not is_object_visible(content, state, oid):
        return False
    return all(c(state, content) for c in defn.contents_visible_when)


def _override(content: GameContent, lid: LocationId, oid: ObjectId) -> ObjectOverride | None:
    return content.locations[lid].object_overrides.get(oid)


def display_name(content: GameContent, lid: LocationId, oid: ObjectId) -> str:
    override = _override(content, lid, oid)
    if override is not None and override.name is not None:
        return override.name
    return content.furniture[oid].name


def description_text(content: GameContent, lid: LocationId, oid: ObjectId) -> Text:
    """Нерезолвленное описание объекта с учётом оверрайда локации.

    Провайдерам действий нужен именно Text: он попадёт в Choice.result_text
    и будет резолвлен в момент применения (session._apply), а не отрисовки.
    """
    override = _override(content, lid, oid)
    if override is not None and override.description is not None:
        return override.description
    return content.furniture[oid].description


def display_description(
    content: GameContent, state: GameState, lid: LocationId, oid: ObjectId
) -> str | None:
    """Описание объекта с учётом оверрайда локации; None, если описания нет."""
    return resolve_text(description_text(content, lid, oid), state, content)
