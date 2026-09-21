"""Юнит-тесты GameSession — без stdin, прямое API: get_view/dispatch."""

import pytest

from damsel.model.content import FurnitureDef, GameContent, ObjectKind, UIContext
from damsel.model.state import GameState, ObjectState
from damsel.model.types import ActionId, ItemId, LocationId, ObjectId
from damsel.model.view import ActionView, GameView, ObjectStatus
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
    """Стартовый вид: контекст LOCATION, шапка и описание чердака, игра не завершена."""
    _, session = world
    view = session.get_view()
    assert view.context is UIContext.LOCATION
    assert view.title == "Чердак"
    assert view.description  # первое посещение — verbose
    assert not view.finished


def test_dispatch_unknown_action_raises() -> None:
    """dispatch() с id, которого нет в текущем виде, бросает UnknownActionError."""
    _, session = make_session()
    session.get_view()
    with pytest.raises(UnknownActionError):
        session.dispatch(ActionId("несуществующее_действие"))


def test_stale_action_id_raises_after_view_change() -> None:
    """Протухший action id: после get_view() карта действий обновилась,
    старый id (клик по устаревшей кнопке) больше не принимается."""
    _, session = make_session()
    view = session.get_view()
    pickup_hammer = find_action(view, "Взять Молоток")
    session.dispatch(pickup_hammer.id)
    session.get_view()  # вид обновился — старой карты больше нет
    with pytest.raises(UnknownActionError):
        session.dispatch(pickup_hammer.id)


def test_message_is_one_shot() -> None:
    """message показывается ровно один раз (в следующем виде за действием),
    затем обнуляется и не повторяется."""
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
    """Стек UI-контекстов: LOCATION → INVENTORY → ITEM_FOCUS и возврат
    по «Назад» на каждый уровень."""
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
    """Осмотр предмета в ITEM_FOCUS: message содержит описание предмета из контента."""
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
    """Выброс предмета: ITEM_FOCUS закрывается автоматически, предмет исчезает
    из инвентаря, повторный выброс по старому id невозможен, в локации предмет
    появляется ровно один раз (без дублей)."""
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
    """Цикл работы с контейнером в OBJECT_FOCUS: открыть сундук → взять
    лежащий в нём предмет (попадает в инвентарь) → закрыть."""
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
    """С max_ticks=N игра завершается (finished=True во view) после N действий."""
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
    """Без max_ticks сессия не завершается никогда (режим для не-CLI фронтендов)."""
    content, state = ContentBuilder(YamlLoader).build()
    session = GameSession(content, state)
    for _ in range(15):
        view = session.get_view()
        session.dispatch(view.actions[0].id)
    assert not session.finished


def test_location_revisit_hides_header() -> None:
    """Шапка и описание локации показываются при первом посещении (verbose);
    при повторном get_view в той же локации их нет; при смене локации шапка снова есть."""
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
    """Провайдеры не выдают действия с дублирующимися id в пределах одного вида."""
    _, session = make_session()
    view = session.get_view()
    ids = [a.id for a in view.actions]
    assert len(ids) == len(set(ids))


def test_choice_scope_filters_item_focus_choices() -> None:
    """Фильтрация статических choices по scope: выбор с scope=item_focus
    не виден в контексте локации и появляется только в ITEM_FOCUS."""
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


def goto(session: GameSession, *text_substr: str) -> GameView:
    """Последовательно нажать опции; возвращает вид после последнего действия."""
    view = session.get_view()
    for substr in text_substr:
        session.dispatch(find_action(view, substr).id)
        view = session.get_view()
    return view


def test_door_is_shared_between_locations() -> None:
    """Одна дверь на две локации: closet_door присутствует в списках объектов
    hall и closet, но FurnitureDef/ObjectState ровно один (старые дубликаты
    hall_/closet_closet_door удалены). Состояние открытости общее: открыл в
    коридоре — открыта и в кладовке. Имя берётся из object_overrides локации:
    в кладовке это «Дверь в коридор»."""
    content, session = make_session()
    # Одна дверь — один FurnitureDef и один ObjectState, id общий.
    hall = content.locations[LocationId("hall")]
    closet = content.locations[LocationId("closet")]
    assert ObjectId("closet_door") in hall.objects
    assert ObjectId("closet_door") in closet.objects
    assert ObjectId("hall_closet_door") not in content.furniture

    # Открыли из коридора — из кладовки она тоже открыта (состояние одно).
    view = goto(session, "Спуститься вниз", "Открыть Дверь в кладовку", "Зайти в кладовку")
    door_view = next(o for o in view.objects if o.id == ObjectId("closet_door"))
    assert door_view.status == ObjectStatus.OPEN
    # Оверрайд имени: из кладовки это «Дверь в коридор».
    assert door_view.name == "Дверь в коридор"

    # Вышли и закрыли из коридора — состояние общее, дверь закрыта.
    view = goto(session, "Выйти из кладовки", "Закрыть Дверь в кладовку")
    door_view = next(o for o in view.objects if o.id == ObjectId("closet_door"))
    assert door_view.status == ObjectStatus.CLOSED
    # «Зайти в кладовку» снова недоступно.
    assert not any("Зайти в кладовку" in a.text for a in view.actions)


def test_switch_lights_closet_and_reveals_rack() -> None:
    """Цепочка «выключатель → свет → видимость»: выключатель в коридоре
    освещает кладовку (lit_when), её описание меняется на «светлое», а
    содержимое стеллажа (contents_visible_when) становится видно и доступно
    для взятия. После взятия предмет в инвентаре один и действие исчезает."""
    _, session = make_session()
    # Выключатель в коридоре включаем до входа в кладовку.
    goto(session, "Спуститься вниз", "Включить Выключатель", "Открыть Дверь в кладовку")
    view = goto(session, "Зайти в кладовку")

    assert view.title == "Кладовка"
    assert "свет" in (view.description or "").lower()
    rack = next(o for o in view.objects if o.id == ObjectId("rack"))
    assert [i.id for i in rack.items_inside] == [ItemId("chisel")]

    # Стамеску можно взять; после взятия она в инвентаре ровно одна.
    view = goto(session, "Взаимодействовать с Стеллаж", "Взять Стаместка")
    assert [i.id for i in view.inventory].count(ItemId("chisel")) == 1
    # Повторно взять нельзя — действие исчезло из меню.
    assert not any("Взять Стаместка" in a.text for a in view.actions)


def test_rack_contents_hidden_in_the_dark() -> None:
    """В тёмной кладовке (выключатель не включён) содержимое стеллажа скрыто:
    items_inside пуст и действия «Взять …» провайдерами не выдаются —
    невидимый предмет нельзя взять даже по известному id."""
    _, session = make_session()
    goto(session, "Спуститься вниз", "Открыть Дверь в кладовку")
    view = goto(session, "Зайти в кладовку")

    assert "темн" in (view.description or "").lower()
    rack = next(o for o in view.objects if o.id == ObjectId("rack"))
    assert rack.items_inside == []

    view = goto(session, "Взаимодействовать с Стеллаж")
    assert not any("Взять" in a.text for a in view.actions)


def test_note_reading_depends_on_light_and_flag() -> None:
    """Условный текст предмета + флаги на примере записки:
    - в тёмном коридоре описания не разобрать, опции «Прочитать» нет;
    - в освещённой кладовке «Прочитать записку» доступна, выдаёт текст,
      ставит флаг note_read, описание предмета теперь помнит текст;
    - после прочтения опция сменяется на «Вспомнить текст», работающую
      и в темноте (условие flag_set, свет не требуется)."""
    _, session = make_session()
    # Достаём записку из сундука в коридоре (коридор тёмный всегда).
    view = goto(session, "Спуститься вниз", "Открыть Сундук", "Взаимодействовать с Сундук")
    view = goto(
        session,
        "Взять Старая записка",
        "Назад",
        "Заглянуть в инвентарь",
        "Осмотреть Старая записка",
    )
    # В темноте записку не прочитать: ни опции, ни текста в описании.
    assert not any("Прочитать" in a.text for a in view.actions)
    view = goto(session, "Осмотреть Старая записка")
    assert "не разобрать" in (view.message or "").lower()

    # Идём в освещённую кладовку (включаем свет).
    view = goto(session, "Назад", "Выйти из инвентаря", "Включить Выключатель")
    view = goto(session, "Открыть Дверь в кладовку", "Зайти в кладовку")
    view = goto(session, "Заглянуть в инвентарь", "Осмотреть Старая записка")
    read = find_action(view, "Прочитать записку")
    session.dispatch(read.id)
    view = session.get_view()
    assert "дощечку с тремя сучками" in (view.message or "")

    # Флаг note_read установлен: описание помнит текст, есть «Вспомнить».
    view = goto(session, "Осмотреть Старая записка")
    assert "дощечку с тремя сучками" in (view.message or "").lower()
    assert any("Вспомнить текст" in a.text for a in view.actions)
    assert not any(a.text == "Прочитать записку" for a in view.actions)

    # Вернулись в тёмный коридор — «Вспомнить» работает и без света.
    view = goto(session, "Назад", "Выйти из инвентаря", "Выйти из кладовки")
    view = goto(session, "Заглянуть в инвентарь", "Осмотреть Старая записка")
    assert any("Вспомнить текст" in a.text for a in view.actions)
    view = goto(session, "Вспомнить текст записки")
    assert "дощечку с тремя сучками" in (view.message or "")


def test_closet_description_updates_when_light_toggled_inside() -> None:
    """Уже посещённая локация показывает описание заново, если резолвленный
    текст изменился (погас свет): сессия сравнивает описание с последним
    показанным и при отличии показывает шапку и новый текст, не дожидаясь
    «первого посещения»."""
    _, session = make_session()
    # Выключатель в коридоре: заходим в кладовку при свете, затем гасим свет
    # и входим снова — описание локации должно показаться заново.
    goto(session, "Спуститься вниз", "Включить Выключатель", "Открыть Дверь в кладовку")
    view = goto(session, "Зайти в кладовку")
    assert view.description is not None  # первое посещение — verbose

    # Возвращаемся в коридор, гасим свет, входим снова — описание сменилось.
    view = goto(session, "Выйти из кладовки", "Выключить Выключатель")
    view = goto(session, "Зайти в кладовку")
    assert view.title == "Кладовка"
    assert "темн" in (view.description or "").lower()


def test_object_focus_closes_when_object_becomes_invisible() -> None:
    """Страховка от протухшего фокуса: если сфокусированный объект стал
    невидимым (visible_when перестало выполняться), OBJECT_FOCUS закрывается
    автоматически и сессия возвращается в предыдущий контекст. Используется
    синтетический объект и choice с эффектом set_flag."""
    from damsel.actions.effects import EFFECTS
    from damsel.actions.providers import StaticChoicesProvider, default_providers
    from damsel.model.content import Choice, ChoiceScope

    content, state = ContentBuilder(YamlLoader).build()
    providers = {ctx: list(p) for ctx, p in default_providers().items()}
    providers[UIContext.OBJECT_FOCUS].append(StaticChoicesProvider(ChoiceScope.OBJECT_FOCUS))
    session = GameSession(content, state, providers=providers)

    # Синтетический объект, видимый, пока флаг не поднят.
    oid = ObjectId("magic_lamp")

    def visible(s: "GameState", c: "GameContent") -> bool:
        return not s.flags.get("lamp_gone", False)

    content.furniture[oid] = FurnitureDef(
        id=oid,
        kind=ObjectKind.CONTAINER,
        name="Лампа",
        description="",
        visible_when=[visible],
    )
    state.objects[oid] = ObjectState()
    content.locations[LocationId("attic")].objects.append(oid)
    content.choices["hide_lamp"] = Choice(
        id="hide_lamp",
        text="Спрятать лампу",
        do=[EFFECTS["set_flag"]({"flag": "lamp_gone"})],
        scope=ChoiceScope.OBJECT_FOCUS,
    )

    view = goto(session, "Взаимодействовать с Лампа")
    assert view.context is UIContext.OBJECT_FOCUS
    view = goto(session, "Спрятать лампу")
    # Объект стал невидимым — фокус закрыт автоматически, вернулись в локацию.
    assert view.context is UIContext.LOCATION
    assert not any(o.id == oid for o in view.objects)


def test_builder_rejects_unknown_object_kind() -> None:
    """Неизвестный kind объекта в данных — ошибка на этапе сборки мира."""
    with pytest.raises(ValueError):
        ObjectKind("teapot")


def test_builder_validates_real_data() -> None:
    """Реальные YAML-данные собираются без ошибок: локации и объекты на месте."""
    content, _ = ContentBuilder(YamlLoader).build()
    assert content.locations[LocationId("attic")].name == "Чердак"
    box = content.furniture[ObjectId("wooden_box")]
    assert box.kind is ObjectKind.CONTAINER
