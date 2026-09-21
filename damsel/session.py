"""GameSession — серверная сторона игры, не зависящая от способа ввода-вывода.

Контракт для фронтендов (CLI, веб, телеграм):
    view = session.get_view()      # ровно один вызов на цикл отображения
    ... показать view, получить ввод ...
    session.dispatch(action.id)    # id — из view.actions, возвращается как есть

get_view() не идемпотентен: потребляет message (one-shot) и отмечает локацию
посещённой. Протухший action_id (клик по устаревшей кнопке) — UnknownActionError,
фронтенд должен показать свежий вид.
"""

from __future__ import annotations

from typing import cast

from damsel.actions.providers import Providers, ProviderContext, default_providers
from damsel.actions.types import Action, GameAction, NavAction, NavKind
from damsel.model.content import Choice, GameContent, UIContext
from damsel.model.state import GameState
from damsel.model.templates import render_template
from damsel.model.types import (
    INVENTORY_LOCATION_ID,
    ActionId,
    ItemId,
    LocationId,
    ObjectId,
)
from damsel.model.view import (
    ActionKind,
    ActionView,
    GameView,
    build_object_views,
    item_view,
)


class UnknownActionError(KeyError):
    """Действие с таким id недоступно в текущем виде (протухший/неверный id)."""


class GameSession:
    def __init__(
        self,
        content: GameContent,
        state: GameState,
        *,
        max_ticks: int | None = None,
        providers: Providers | None = None,
    ) -> None:
        self._content = content
        self._state = state
        self._max_ticks = max_ticks
        self._providers: Providers = (
            providers if providers is not None else default_providers()
        )
        self._ui: list[UIContext] = [UIContext.LOCATION]
        self._focused_item: ItemId | None = None
        self._focused_object: ObjectId | None = None
        self._message: str | None = None
        self._ticks = 0
        self._prev_location: LocationId = state.current_location
        self._actions: dict[ActionId, Action] = {}

    @property
    def finished(self) -> bool:
        return self._max_ticks is not None and self._ticks >= self._max_ticks

    def get_view(self) -> GameView:
        ctx = self._ui[-1]
        title: str | None = None
        description: str | None = None
        objects = []
        floor_items = []

        if ctx is UIContext.LOCATION:
            location_id = self._state.current_location
            location = self._content.locations[location_id]
            verbose = location_id not in self._state.visited_locations
            changed = location_id != self._prev_location
            if verbose or changed:
                title = location.name
                description = location.description if verbose else None
                self._state.set_location_visited()
            objects = build_object_views(self._content, self._state, location_id, verbose)
            floor_items = [
                item_view(self._content, iid)
                for iid in self._state.locations_items[location_id]
            ]
            self._prev_location = location_id

        actions = self._collect_actions(ctx)
        inventory = [
            item_view(self._content, iid)
            for iid in self._state.locations_items[INVENTORY_LOCATION_ID]
        ]
        message = self._message
        self._message = None

        return GameView(
            context=ctx,
            title=title,
            description=description,
            objects=objects,
            floor_items=floor_items,
            inventory=inventory,
            message=message,
            actions=[self._action_view(a) for a in actions],
            finished=self.finished,
        )

    def dispatch(self, action_id: ActionId) -> None:
        action = self._actions.get(action_id)
        if action is None:
            raise UnknownActionError(action_id)
        match action:
            case NavAction():
                self._navigate(action)
            case GameAction():
                self._message = self._apply(action.choice)
                self._sync_focus()
        self._ticks += 1

    def _sync_focus(self) -> None:
        """Фокус на предмете валиден, пока предмет в инвентаре.

        После выброса/использования предмета закрываем ITEM_FOCUS и возвращаемся
        в предыдущий контекст — иначе провайдеры продолжат предлагать действия
        для предмета, которого уже нет в инвентаре.
        """
        if self._ui[-1] is not UIContext.ITEM_FOCUS:
            return
        inv = self._state.locations_items[INVENTORY_LOCATION_ID]
        if self._focused_item is None or self._focused_item not in inv:
            self._ui.pop()
            self._focused_item = None

    def _collect_actions(self, ctx: UIContext) -> list[Action]:
        provider_ctx = ProviderContext(
            state=self._state,
            content=self._content,
            ui_context=ctx,
            focused_item=self._focused_item,
            focused_object=self._focused_object,
        )
        actions: list[Action] = []
        for provider in self._providers.get(ctx, []):
            actions.extend(provider.provide(provider_ctx))
        ids = [a.id for a in actions]
        if len(ids) != len(set(ids)):
            duplicates = {i for i in ids if ids.count(i) > 1}
            raise RuntimeError(f"Провайдеры выдали дублирующиеся id действий: {duplicates}")
        self._actions = {a.id: a for a in actions}
        return actions

    @staticmethod
    def _action_view(action: Action) -> ActionView:
        kind = ActionKind.NAV if isinstance(action, NavAction) else ActionKind.GAME
        return ActionView(id=action.id, text=action.text, kind=kind)

    def _apply(self, choice: Choice) -> str | None:
        # Повторная проверка условий: защита от протухшего вида (stale action id).
        if not choice.is_available(self._state, self._content):
            raise RuntimeError("Conditions not met")
        for effect in choice.do:
            effect(self._state, self._content)
        if choice.result_text is not None:
            return choice.result_text
        if choice.result is not None:
            return render_template(choice.result, self._content)
        return None

    def _navigate(self, nav: NavAction) -> None:
        match nav.kind:
            case NavKind.BACK:
                if len(self._ui) > 1:
                    self._ui.pop()
                    self._focused_item = None
                    self._focused_object = None
            case NavKind.OPEN_INVENTORY:
                self._ui.append(UIContext.INVENTORY)
            case NavKind.FOCUS_ITEM:
                self._focused_item = cast(ItemId, nav.target)
                self._ui.append(UIContext.ITEM_FOCUS)
            case NavKind.FOCUS_OBJECT:
                self._focused_object = cast(ObjectId, nav.target)
                self._ui.append(UIContext.OBJECT_FOCUS)
