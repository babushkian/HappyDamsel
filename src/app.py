from typing import Callable
from dataclasses import dataclass, field
import yaml
from pathlib import Path
from pprint import pprint

CONTENT_DIR = Path(__file__).resolve().parent / "world"

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
class Item:
    id: ItemId
    name: str
    description: str
    consumable: bool = False


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

ITEMS: dict[ItemId, Item] = {}
LOCATIONS: dict[LocationId, Location] = {}
CHOICES_RAW: dict[str, dict] = {}

def load_choices_raw(data: dict):
    for cid, raw in data["choices"].items():
        CHOICES_RAW[cid] = raw

content_file =CONTENT_DIR / "choices.yaml"
with content_file.open(mode="r", encoding="utf-8") as file:
    yaml_choices = yaml.safe_load(file.read())
load_choices_raw(yaml_choices)

with (CONTENT_DIR / "items.yaml").open(mode="r", encoding="utf-8") as file:
    raw_item_data = yaml.safe_load(file.read())
with (CONTENT_DIR / "locations.yaml").open(mode="r", encoding="utf-8") as file:
    raw_location_data = yaml.safe_load(file.read())

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
# GOLD_RING = ItemId("gold_ring")
BOX = ObjectId("wooden_box")
# CHEST = ObjectId("iron_chest")
ATTIC = LocationId("attic")
# HALL = LocationId("hall")


def build_item(iid: str,  data: dict):
    item_id = ItemId(iid)
    ITEMS[item_id] = Item(
            id=item_id,
            name=data["name"],
            description=data["description"],
            consumable=data["consumable"],
        )


def build_location( lid: str,  data: dict):
    location_id = LocationId(lid)
    loc = Location(
        id=location_id,
        name=data["name"],
        description=data["description"],
        containers={},
    )
    containers:dict[ObjectId, Container] = {}
    for cid, cont_data in data.get("containers", {}).items():
        container_id = ObjectId(cid)
        containers[container_id] = Container(
            id=container_id,
            locked=cont_data["locked"],
            open=cont_data["open"],
            contents=[ItemId(iid) for iid in cont_data.get("contents", [])]
        )
    loc.containers = containers
    LOCATIONS[location_id] = loc

for  iid, raw in raw_item_data.items():
    build_item(iid, raw)

for  lid, raw in raw_location_data.items():
    build_location(lid, raw)

pprint(ITEMS)
# инвентарь с ключом
inventory = Inventory(items={RUSTY_KEY: 1})

# состояние игры
state = GameState(
    current_location=ATTIC,
    # locations={ATTIC: attic_loc, HALL: hall_loc},
    locations=LOCATIONS,
    inventory=inventory,
    flags={},
)


CHOICES: dict[str, Choice]={}
def build_choice(state: GameState, cid: str,  data: dict):
    conditions: list[Condition] = []
    for c in data.get("conditions", []):
        conditions.append( CONDITIONS[c["type"]](state, c))
    effects: list[Effect] = []
    for e in data.get("effects", []):
        effects.append( EFFECTS[e["type"]](state, e))
    CHOICES[cid] = Choice(
        id=cid,
        text=data["text"],
        when=conditions,
        do=effects
    )

for  cid, struct in CHOICES_RAW.items():
    build_choice(state, cid, struct)

open_box = CHOICES["open_box"]
go_down = CHOICES["go_down_to_hall"]
up_to_attic = CHOICES["go_up_to_attic"]


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
    state.get_container(BOX)  # BOX осталась в локации Чердак
except ValueError as exc:
    print("Ошибка доступа к контейнеру:", exc)

if up_to_attic.is_available():
    up_to_attic.apply()
    print("После перемещения наверх — локация:", state.location().name)