from typing import Callable, Self
from dataclasses import dataclass, field


class Identifier(str):
    def __new__(cls, value: str) -> Self:
        return super().__new__(cls, value)

    @property
    def value(self) -> str:
        return str(self)

class ItemId(Identifier):
    pass

class ObjectId(Identifier):
    pass

class LocationId(Identifier):
    pass

@dataclass
class Item:
    id: ItemId
    name: str
    description: str
    consumable: bool = False

    def describe(self, verbose: bool) -> str:
        if verbose:
            return f"{self.name}. {self.description}"
        return f"{self.name.lower()}"

@dataclass
class Container:
    id: ObjectId
    name: str
    description: str
    locked: bool
    open: bool
    contents: list[ItemId]

    def describe(self, verbose: bool) -> str:
        status = "(закрыто)" if not self.open else ""
        status = "(заперто)" if self.locked else status
        if verbose:
            return f"{self.name} {status}. {self.description}"
        return f"{self.name} {status}"


@dataclass
class Location:
    id: LocationId
    name: str
    visited: bool = False
    description: str = ""
    containers: dict[ObjectId, Container] = field(default_factory=dict) # переписать сс словаря на список ObjectId
    items: list[ItemId] = field(default_factory=list)

    def describe(self, verbose: bool) -> str:
        if verbose:
            return f"{self.name}\n{self.description}"
        return self.name

    def set_visited(self) -> None:
        self.visited = True


@dataclass
class Inventory:
    items: dict[ItemId, int]

    def has(self, item: ItemId) -> bool:
        return self.items.get(item, 0) > 0

    def add(self, item: ItemId, qty: int = 1) -> None:
        self.items[item] = self.items.get(item, 0) + qty

    def remove(self, item: ItemId, qty: int = 1) -> None:
        if self.items.get(item, 0) < qty:
            raise ValueError("Item not in inventory")
        if self.items[item] == qty:
            del self.items[item]
        else:
            self.items[item] -= qty


Condition = Callable[["GameState"], bool]
Effect = Callable[["GameState"], None]


@dataclass
class Choice:
    id: str
    text: str
    description: str
    when: list[Condition] = field(default_factory=list)
    do: list[Effect] = field(default_factory=list)

    def is_available(self, state: "GameState") -> bool:
        return all(cond(state) for cond in self.when)

    def apply(self, state: "GameState") -> str:
        if not self.is_available(state):
            raise RuntimeError("Conditions not met")
        for effect in self.do:
            effect(state)
        return self.description


@dataclass
class GameState:
    current_location: LocationId
    inventory: Inventory
    return_location: LocationId | None = None
    locations: dict[LocationId, Location] = field(default_factory=dict)
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




