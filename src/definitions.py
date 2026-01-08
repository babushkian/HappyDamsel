from typing import Callable
from dataclasses import dataclass, field


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
    name: str
    description: str
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


Condition = Callable[[GameState], bool]
Effect = Callable[[GameState], None]


@dataclass
class Choice:
    id: str
    text: str
    when: list[Condition]
    do: list[Effect]

    def is_available(self, state: GameState) -> bool:
        return all(cond(state) for cond in self.when)

    def apply(self, state: GameState) -> None:
        if not self.is_available(state):
            raise RuntimeError("Conditions not met")
        for effect in self.do:
            effect(state)

