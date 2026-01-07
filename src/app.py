from typing import Callable
from dataclasses import dataclass, field
import yaml
from pathlib import Path
from pprint import pprint

CONTENT_DIR = Path(__file__).resolve().parent / "world"
print(CONTENT_DIR)
content_file =CONTENT_DIR / "choices.yaml"
print(content_file, content_file.exists())

with content_file.open(mode="r", encoding="utf-8") as file:
    yaml_data = yaml.safe_load(file.read())
pprint(yaml_data)

@dataclass(frozen=True)
class ItemId:
    value: str

@dataclass(frozen=True)
class ObjectId:
    value: str

@dataclass(frozen=True)
class LocationId:
    value: str

@dataclass(frozen=True)
class LocationId:
    value: str


@dataclass
class Container:
    id: ObjectId
    locked: bool
    open: bool
    contents: list[ItemId]

@dataclass
class Location:
    id: LocationId
    name: str
    description: str = ""
    containers: dict[ObjectId, Container] = field(default_factory=dict)



@dataclass
class Inventory:
    items: dict[ItemId, int]
    def has(self, item: ItemId) -> bool:
        return self.items.get(item, 0) > 0

    def add(self, item: ItemId, qty: int = 1):
        self.items[item] = self.items.get(item, 0) + qty

    def remove(self, item: ItemId, qty: int = 1):
        if self.items.get(item, 0) < qty:
            raise ValueError("Item not in inventory")
        if self.items[item] == qty:
            del self.items[item]
        else:
            self.items[item] -= qty



@dataclass
class GameState:
    current_location: LocationId
    locations: dict[LocationId, Location] = field(default_factory=dict)
    inventory: Inventory = field(default_factory=Inventory)
    flags: dict[str, bool] = field(default_factory=dict)
    def location(self) -> Location:
        return self.locations[self.current_location]

    def move_to(self, lid: LocationId) -> None:
        if lid not in self.locations:
            raise ValueError(f"Location {lid.value!r} does not exist")
        self.current_location = lid

    def get_container(self, cid: ObjectId) -> Container:
        """ Возвращает контейнер только из текущей локации.
        Если контейнера нет в текущей локации — ValueError.
        Это соответствует ограничению: игрок может взаимодействовать только с контейнерами в текущей локации. """
        loc = self.location()
        if cid not in loc.containers:
            raise ValueError(f"Container {cid.value!r} not found in current location {loc.id.value!r}")
        return loc.containers[cid]






#-------------------------
#-------------------------
Condition = Callable[[], bool]
Effect = Callable[[], None]
ConditionFactory = Callable[[GameState, dict], Condition]
EffectFactory = Callable[[GameState, dict], Effect]

CONDITIONS: dict[str, ConditionFactory] = {}
EFFECTS: dict[str, EffectFactory] = {}

def register_condition(name: str):
    def decorator(fn: ConditionFactory):
        CONDITIONS[name] = fn
        return fn
    return decorator


def register_effect(name: str):
    def decorator(fn: EffectFactory):
        EFFECTS[name] = fn
        return fn
    return decorator

#-------------------- условия

@register_condition("has_item")
def has_item(state: GameState, data: dict) -> Condition:
    item = ItemId(data["item"])
    def _cond() -> bool:
        return state.inventory.has(item)
    return _cond

@register_condition("container_locked")
def container_locked(state: GameState, data: dict) -> Condition:
    cid = ObjectId(data["container"])

    def _cond() -> bool:
        try:
            return state.get_container(cid).locked
        except ValueError:
            return False
    return _cond


#-------------------- эффекты
@register_effect("consume_item")
def make_consume_item(state: GameState, data: dict):
    item = ItemId(data["item"])

    def _effect():
        state.inventory.remove(item)

    return _effect

@register_effect("unlock_container")
def make_unlock_and_open(state: GameState, data: dict) -> Effect:
    cid = ObjectId(data["container"])

    def _effect() -> None:
        c = state.get_container(cid)
        c.locked = False
        c.open = True
    return _effect

@register_effect("reveal_contents")
def make_reveal_contents(state: GameState, data: dict) -> Effect:
    cid = ObjectId(data["container"])
    def _effect() -> None:
        c = state.get_container(cid)
        for item in c.contents:
            state.inventory.add(item)
        c.contents.clear()
    return _effect

@register_effect("move_to")
def make_move_to(state: GameState, data: dict) -> Effect:
    lid = LocationId(data["location"])
    def _effect() -> None:
        state.move_to(lid)
    return _effect


@dataclass
class Choice:
    id: str
    text: str
    when: list[Condition]
    do: list[Effect]

    def is_available(self) -> bool:
        return all(cond() for cond in self.when)

    def apply(self) -> None:
        if not self.is_available():
            raise RuntimeError("Conditions not met")
        for effect in self.do:
            effect()





# идентификаторы
RUSTY_KEY = ItemId("rusty_key")
GOLD_RING = ItemId("gold_ring")
BOX = ObjectId("wooden_box")
CHEST = ObjectId("iron_chest")
ATTIC = LocationId("attic")
HALL = LocationId("hall")

# локации
attic_loc = Location(
    id=ATTIC, name="Чердак", description="Пыльный чердак со старой шкатулкой."
)
hall_loc = Location(id=HALL, name="Прихожая", description="Низ под чердаком.")

# контейнеры привязаны к локациям (только в текущей локации доступны)
attic_loc.containers[BOX] = Container(
    id=BOX,
    locked=True,
    open=False,
    contents=[GOLD_RING]
)

hall_loc.containers[CHEST] = Container(
    id=CHEST,
    locked=False,
    open=True,
    contents=[ItemId("note")]
)

# инвентарь с ключом
inventory = Inventory(items={RUSTY_KEY: 1})

# состояние игры
state = GameState(
    current_location=ATTIC,
    locations={ATTIC: attic_loc, HALL: hall_loc},
    inventory=inventory,
    flags={},
)


open_box = Choice(
    id="open_box",
    text="Открыть шкатулку",
    when=[
        CONDITIONS["has_item"](state, {"item": "rusty_key"}),
        CONDITIONS["container_locked"](state, {"container": "wooden_box"}),
    ],
    do=[
        EFFECTS["consume_item"](state, {"item": "rusty_key"}),
        EFFECTS["unlock_container"](state, {"container": "wooden_box"}),
        EFFECTS["reveal_contents"](state, {"container": "wooden_box"}),
    ],
)

go_down = Choice(
    id="go_down",
    text="Спуститься вниз",
    when=[],
    do=[EFFECTS["move_to"](state, {"location": "hall"})],
)



# Демонстрация (без async — просто последовательное применение)
def show_inventory(inv: Inventory):
    return {k.value: v for k, v in inv.items.items()}


print("Текущая локация:", state.location().name)  # Чердак
print("Инвентарь до:", show_inventory(state.inventory))

# Попробуем открыть шкатулку в чердаке
if open_box.is_available():
    open_box.apply()
    print("Шкатулка открыта, содержимое добавлено в инвентарь.")
else:
    print("Условия для открытия шкатулки не выполнены.")

print("Инвентарь после:", show_inventory(state.inventory))

# Перейдём вниз (через эффект)
if go_down.is_available():
    go_down.apply()
    print("После перемещения — локация:", state.location().name)

# Попытка получить контейнер, который не в текущей локации — выдаст ошибку
try:
    state.get_container(BOX)  # BOX теперь не в прихожей
except ValueError as exc:
    print("Ошибка доступа к контейнеру:", exc)
