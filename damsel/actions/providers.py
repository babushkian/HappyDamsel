"""Провайдеры действий: каждый отвечает за один источник доступных действий.

Сессия компонирует провайдеров по текущему UI-контексту (см. default_providers).
Провайдеры не имеют состояния и не знают ни о способе ввода-вывода, ни друг о друге.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass

from damsel.actions.effects import EFFECTS
from damsel.actions.types import Action, GameAction, NavAction, NavKind
from damsel.model.content import (
    Choice,
    ChoiceScope,
    GameContent,
    Result,
    UIContext,
)
from damsel.model.state import GameState
from damsel.model.types import ActionId, ItemId, ObjectId, INVENTORY_LOCATION_ID


@dataclass(frozen=True)
class ProviderContext:
    state: GameState
    content: GameContent
    ui_context: UIContext
    focused_item: ItemId | None = None
    focused_object: ObjectId | None = None


class ActionProvider:
    """Интерфейс провайдера действий для одного или нескольких UI-контекстов."""

    def provide(self, ctx: ProviderContext) -> Iterator[Action]:
        raise NotImplementedError


def _nav(
    id_: str, text: str, kind: NavKind, target: ItemId | ObjectId | None = None
) -> NavAction:
    return NavAction(id=ActionId(id_), text=text, kind=kind, target=target)


def _pickup_choice(iid: ItemId, name: str) -> Choice:
    return Choice(
        id=f"pick_up_{iid}",
        text=f"Взять {name}",
        result=Result("generic_pickup", {"item": iid}),
        do=[EFFECTS["get_item"]({"item": iid})],
    )


class StaticChoicesProvider(ActionProvider):
    """Статические выборы из YAML, отфильтрованные по scope и условиям."""

    def __init__(self, scope: ChoiceScope) -> None:
        self.scope = scope

    def provide(self, ctx: ProviderContext) -> Iterator[Action]:
        for choice in ctx.content.choices.values():
            if choice.scope is self.scope and choice.is_available(ctx.state, ctx.content):
                yield GameAction(choice)


class FloorItemsProvider(ActionProvider):
    """«Взять X» для предметов, лежащих в текущей локации."""

    def provide(self, ctx: ProviderContext) -> Iterator[Action]:
        choices = [
            _pickup_choice(iid, ctx.content.items[iid].name)
            for iid in ctx.state.locations_items[ctx.state.current_location]
        ]
        choices.sort(key=lambda c: c.text)
        for choice in choices:
            yield GameAction(choice)


class ContainerActionsProvider(ActionProvider):
    """Открыть/закрыть фурнитуру; в фокусе объекта — ещё и взять из контейнера."""

    def _targets(self, ctx: ProviderContext) -> list[ObjectId]:
        if ctx.ui_context is UIContext.OBJECT_FOCUS and ctx.focused_object is not None:
            return [ctx.focused_object]
        return list(ctx.content.locations[ctx.state.current_location].objects)

    def provide(self, ctx: ProviderContext) -> Iterator[Action]:
        targets = self._targets(ctx)
        for oid in targets:
            furn = ctx.content.furniture[oid]
            obj = ctx.state.objects[oid]
            if furn.can_open and not obj.is_open and not obj.is_locked:
                yield GameAction(
                    Choice(
                        id=f"open_{oid}",
                        text=f"Открыть {furn.name}",
                        result=Result("generic_open", {"object": oid}),
                        do=[EFFECTS["open_object"]({"object": oid})],
                    )
                )
        for oid in targets:
            furn = ctx.content.furniture[oid]
            obj = ctx.state.objects[oid]
            if furn.can_open and obj.is_open and not obj.is_locked:
                yield GameAction(
                    Choice(
                        id=f"close_{oid}",
                        text=f"Закрыть {furn.name}",
                        result=Result("generic_close", {"object": oid}),
                        do=[EFFECTS["close_object"]({"object": oid})],
                    )
                )
        if ctx.ui_context is UIContext.OBJECT_FOCUS:
            for oid in targets:
                furn = ctx.content.furniture[oid]
                obj = ctx.state.objects[oid]
                if furn.is_container and obj.is_open:
                    for iid in obj.items:
                        yield GameAction(
                            Choice(
                                id=f"take_from_{oid}_{iid}",
                                text=f"Взять {ctx.content.items[iid].name}",
                                do=[EFFECTS["get_item"]({"item": iid})],
                                result=Result("generic_pickup", {"item": iid}),
                            )
                        )


class ObjectFocusProvider(ActionProvider):
    """Осмотр сфокусированного объекта."""

    def provide(self, ctx: ProviderContext) -> Iterator[Action]:
        if ctx.focused_object is None:
            return
        furn = ctx.content.furniture[ctx.focused_object]
        yield GameAction(
            Choice(
                id=f"examine_{ctx.focused_object}",
                text=f"Осмотреть: {furn.name}",
                result_text=furn.description,
                do=[],
            )
        )


class ItemFocusProvider(ActionProvider):
    """Осмотр и выброс сфокусированного предмета."""

    def provide(self, ctx: ProviderContext) -> Iterator[Action]:
        if ctx.focused_item is None:
            return
        item = ctx.content.items[ctx.focused_item]
        yield GameAction(
            Choice(
                id=f"examine_{ctx.focused_item}",
                text=f"Осмотреть {item.name}",
                result_text=item.description,
                do=[],
            )
        )
        yield GameAction(
            Choice(
                id=f"drop_{ctx.focused_item}",
                text=f"Выбросить {item.name}",
                result=Result("generic_drop", {"item": ctx.focused_item}),
                do=[EFFECTS["drop_item"]({"item": ctx.focused_item})],
            )
        )


class InventoryProvider(ActionProvider):
    """Список предметов инвентаря как навигация фокуса."""

    def provide(self, ctx: ProviderContext) -> Iterator[Action]:
        for iid in ctx.state.locations_items[INVENTORY_LOCATION_ID]:
            item = ctx.content.items[iid]
            yield _nav(f"nav:item:{iid}", f"Осмотреть {item.name}", NavKind.FOCUS_ITEM, iid)


class NavigationProvider(ActionProvider):
    """Кнопки навигации: инвентарь, фокус на объектах локации, «назад»."""

    def provide(self, ctx: ProviderContext) -> Iterator[Action]:
        match ctx.ui_context:
            case UIContext.LOCATION:
                yield _nav("nav:inventory", "Заглянуть в инвентарь", NavKind.OPEN_INVENTORY)
                location = ctx.content.locations[ctx.state.current_location]
                for oid in location.objects:
                    furn = ctx.content.furniture[oid]
                    yield _nav(
                        f"nav:obj:{oid}",
                        f"Взаимодействовать с {furn.name}",
                        NavKind.FOCUS_OBJECT,
                        oid,
                    )
            case UIContext.INVENTORY:
                yield _nav("nav:back", "Выйти из инвентаря.", NavKind.BACK)
            case UIContext.ITEM_FOCUS | UIContext.OBJECT_FOCUS:
                yield _nav("nav:back", "Назад.", NavKind.BACK)
            case _:
                return


def default_providers() -> dict[UIContext, list[ActionProvider]]:
    """Композиция провайдеров по контекстам. Порядок определяет порядок опций в UI."""
    return {
        UIContext.LOCATION: [
            StaticChoicesProvider(ChoiceScope.LOCATION),
            FloorItemsProvider(),
            ContainerActionsProvider(),
            NavigationProvider(),
        ],
        UIContext.INVENTORY: [
            InventoryProvider(),
            NavigationProvider(),
        ],
        UIContext.ITEM_FOCUS: [
            ItemFocusProvider(),
            StaticChoicesProvider(ChoiceScope.ITEM_FOCUS),
            NavigationProvider(),
        ],
        UIContext.OBJECT_FOCUS: [
            ObjectFocusProvider(),
            ContainerActionsProvider(),
            NavigationProvider(),
        ],
    }


Providers = Mapping[UIContext, Sequence[ActionProvider]]
