"""Юнит-тесты GameSession — без stdin, прямое API: get_view/dispatch."""

import pytest

from damsel.model.content import GameContent, ObjectKind, UIContext
from damsel.model.types import ActionId, ItemId, LocationId, ObjectId
from damsel.model.view import ActionView, GameView
from damsel.session import GameSession, UnknownActionError
from damsel.world.builder import ContentBuilder
from damsel.world.loader import YamlLoader


@pytest.fixture()
def world() -> tuple[GameContent, GameSession]:
    content, state = ContentBuilder(YamlLoader).build()
    return content, GameSession(content, state)


def make_session() -> tuple[GameContent, GameSession]:
    content, state = ContentBuilder(YamlLoader).build()
    return content, GameSession(content, state)


def find_action(view: GameView, text_substr: str) -> ActionView:
    matches = [a for a in view.actions if text_substr.lower() in a.text.lower()]
    assert len(matches) == 1, f"{text_substr!r}: найдено {matches}"
    return matches[0]


def test_initial_view(world: tuple[GameContent, GameSession]) -> None:
    _, session = world
    view = session.get_view()
    assert view.context is UIContext.LOCATION
    assert view.title == "Чердак"
    assert view.description  # первое посещение — verbose
    assert not view.finished


def test_dispatch_unknown_action_raises() -> None:
    _, session = make_session()
    session.get_view()
    with pytest.raises(UnknownActionError):
        session.dispatch(ActionId("несуществующее_действие"))


def test_stale_action_id_raises_after_view_change() -> None:
    _, session = make_session()
    view = session.get_view()
    pickup_hammer = find_action(view, "Взять Молоток")
    session.dispatch(pickup_hammer.id)
    session.get_view()  # вид обновился — старой карты больше нет
    with pytest.raises(UnknownActionError):
        session.dispatch(pickup_hammer.id)


def test_message_is_one_shot() -> None:
    _, session = make_session()
    view = session.get_view()
    pickup = find_action(view, "Взять Молоток")
    session.dispatch(pickup.id)
    assert session.get_view().message == "Ты подобрал Молоток."
    # следующее действие — навигация, message не повторяется
    view = session.get_view()
    session.dispatch(find_action(view, "Заглянуть в инвентарь").id)
    assert session.get_view().message is None


def test_inventory_navigation_stack() -> None:
    _, session = make_session()
    view = session.get_view()
    session.dispatch(find_action(view, "Заглянуть в инвентарь").id)

    view = session.get_view()
    assert view.context is UIContext.INVENTORY
    assert view.title is None  # шапка локации не показывается
    session.dispatch(find_action(view, "Осмотреть Ржавый ключ").id)

    view = session.get_view()
    assert view.context is UIContext.ITEM_FOCUS
    session.dispatch(find_action(view, "Назад").id)

    view = session.get_view()
    assert view.context is UIContext.INVENTORY
    session.dispatch(find_action(view, "Выйти из инвентаря").id)
    assert session.get_view().context is UIContext.LOCATION


def test_item_focus_examine_and_drop() -> None:
    content, session = make_session()
    view = session.get_view()
    session.dispatch(find_action(view, "Взять Молоток").id)
    view = session.get_view()
    session.dispatch(find_action(view, "Заглянуть в инвентарь").id)
    view = session.get_view()
    session.dispatch(find_action(view, "Осмотреть Молоток").id)
    view = session.get_view()
    session.dispatch(find_action(view, "Осмотреть Молоток").id)
    assert session.get_view().message == content.items[ItemId("hammer")].description


def test_drop_item_exits_focus_and_cannot_be_repeated() -> None:
    _, session = make_session()
    view = session.get_view()
    session.dispatch(find_action(view, "Взять Молоток").id)
    view = session.get_view()
    session.dispatch(find_action(view, "Заглянуть в инвентарь").id)
    view = session.get_view()
    session.dispatch(find_action(view, "Осмотреть Молоток").id)
    view = session.get_view()
    assert view.context is UIContext.ITEM_FOCUS
    drop = find_action(view, "Выбросить Молоток")
    session.dispatch(drop.id)

    # После выброса фокус закрыт, вернулись в инвентарь без молотка
    view = session.get_view()
    assert view.context is UIContext.INVENTORY
    assert all(i.id != ItemId("hammer") for i in view.inventory)
    assert not any("Выбросить" in a.text for a in view.actions)

    # Старый id «выбросить» больше не действует
    with pytest.raises(UnknownActionError):
        session.dispatch(drop.id)

    # Молоток лежит в локации — и только один раз
    session.dispatch(find_action(view, "Выйти из инвентаря").id)
    view = session.get_view()
    assert [i.id for i in view.floor_items].count(ItemId("hammer")) == 1


def test_object_focus_open_take_close() -> None:
    _, session = make_session()
    # спуститься в коридор
    view = session.get_view()
    session.dispatch(find_action(view, "Спуститься вниз").id)
    view = session.get_view()
    session.dispatch(find_action(view, "Взаимодействовать с Сундук").id)
    view = session.get_view()
    assert view.context is UIContext.OBJECT_FOCUS
    session.dispatch(find_action(view, "Открыть Сундук").id)
    view = session.get_view()
    session.dispatch(find_action(view, "Взять Старая записка").id)
    view = session.get_view()
    assert any(i.id == ItemId("note") for i in view.inventory)
    session.dispatch(find_action(view, "Закрыть Сундук").id)


def test_max_ticks_finishes() -> None:
    content, state = ContentBuilder(YamlLoader).build()
    session = GameSession(content, state, max_ticks=2)
    assert not session.finished
    view = session.get_view()
    session.dispatch(view.actions[0].id)
    assert not session.finished
    view = session.get_view()
    session.dispatch(view.actions[0].id)
    assert session.finished
    assert session.get_view().finished


def test_no_max_ticks_never_finishes() -> None:
    content, state = ContentBuilder(YamlLoader).build()
    session = GameSession(content, state)
    for _ in range(15):
        view = session.get_view()
        session.dispatch(view.actions[0].id)
    assert not session.finished


def test_location_revisit_hides_header() -> None:
    _, session = make_session()
    view = session.get_view()  # первое посещение — verbose
    session.dispatch(find_action(view, "Взять Молоток").id)
    view = session.get_view()  # та же локация, уже посещена — без шапки
    assert view.title is None
    assert view.description is None
    session.dispatch(find_action(view, "Спуститься вниз").id)
    view = session.get_view()  # смена локации — шапка снова есть
    assert view.title == "Коридор"


def test_action_ids_are_unique_per_view() -> None:
    _, session = make_session()
    view = session.get_view()
    ids = [a.id for a in view.actions]
    assert len(ids) == len(set(ids))


def test_choice_scope_filters_item_focus_choices() -> None:
    from damsel.actions.conditions import CONDITIONS
    from damsel.model.content import Choice, ChoiceScope

    content, session = make_session()
    # Синтетический выбор с scope=item_focus: доступен только при наличии молотка
    # и должен появиться только в контексте фокуса на предмете.
    hammer_choice = Choice(
        id="use_hammer",
        text="Забить гвоздь Молотком",
        when=[CONDITIONS["has_item"]({"item": "hammer"})],
        do=[],
        scope=ChoiceScope.ITEM_FOCUS,
        result_text="Ты забил гвоздь.",
    )
    content.choices["use_hammer"] = hammer_choice

    # В локации его быть не должно
    view = session.get_view()
    assert all(a.text != hammer_choice.text for a in view.actions)

    # Подбираем молоток, заходим в инвентарь, фокус на молотке
    session.dispatch(find_action(view, "Взять Молоток").id)
    view = session.get_view()
    session.dispatch(find_action(view, "Заглянуть в инвентарь").id)
    view = session.get_view()
    session.dispatch(find_action(view, "Осмотреть Молоток").id)
    view = session.get_view()
    assert view.context is UIContext.ITEM_FOCUS
    action = find_action(view, "Забить гвоздь")
    session.dispatch(action.id)
    assert session.get_view().message == "Ты забил гвоздь."


def test_builder_rejects_unknown_object_kind() -> None:
    with pytest.raises(ValueError):
        ObjectKind("teapot")


def test_builder_validates_real_data() -> None:
    content, _ = ContentBuilder(YamlLoader).build()
    assert content.locations[LocationId("attic")].name == "Чердак"
    box = content.furniture[ObjectId("wooden_box")]
    assert box.kind is ObjectKind.CONTAINER
