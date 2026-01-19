from typing import Callable, Self, NewType
from dataclasses import dataclass, field


ItemId = NewType("ItemId", str)
ObjectId = NewType("ObjectId", str)
LocationId = NewType("LocationId", str)

@dataclass(frozen=True)
class ItemDef:
    id: ItemId
    name: str
    description: str
    consumable: bool

@dataclass(frozen=True)
class FurnitureDef:
    id: ObjectId
    kind: str                   # "door", "container", "shelf", "jar"
    name: str
    description: str

    # поведенческие характеристики
    can_open: bool = False
    can_lock: bool = False
    is_container: bool = False
    is_transparent: bool = False
    turnable: bool = False


@dataclass(frozen=True)
class ExitDef:
    target: LocationId
    text: str                     # "Пойти на кухню"
    when: list["Condition"] = field(default_factory=list)
    do: list["Effect"] = field(default_factory=list)


@dataclass(frozen=True)
class LocationDef:
    id: LocationId
    name: str
    description: str
    objects: list[ObjectId]
    items: list[ItemId]
    # exits: list[ExitDef]

@dataclass
class ObjectState:
    flags: dict[str, bool] = field(default_factory=dict)
    items: list[ItemId] = field(default_factory=list)



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


Condition = Callable[["GameState", "GameContent"], bool]
Effect = Callable[["GameState", "GameContent"], None]


@dataclass
class Choice:
    id: str
    text: str
    when: list[Condition] = field(default_factory=list)
    do: list[Effect] = field(default_factory=list)
    result_text: str | None = None
    result_renderer: Callable[["GameState"], str]| None = None

    def is_available(self, state: "GameState", content: "GameContent") -> bool:
        return all(cond(state, content) for cond in self.when)

    def apply(self, state: "GameState", content: "GameContent") -> str:
        if not self.is_available(state, content):
            raise RuntimeError("Conditions not met")
        for effect in self.do:
            effect(state, content)

        if self.result_text is not None:
            return self.result_text
        if self.result_renderer is not None:
            return self.result_renderer(state)
        return ""


@dataclass
class GameState:
    current_location: LocationId
    inventory: Inventory
    return_location: LocationId | None = None
    locations_items: dict[LocationId, list[ItemId]] = field(default_factory=dict)
    objects: dict[ObjectId, ObjectState] = field(default_factory=dict)
    visited_locations: set[LocationId] = field(default_factory=set)
    flags: dict[str, bool] = field(default_factory=dict,)

    def move_to(self, lid: LocationId) -> None:
        if lid not in self.locations:
            raise ValueError(f"Location {lid.value!r} does not exist")
        self.current_location = lid

    def set_location_visited(self) -> None:
        if self.current_location not in self.visied_locations:
            self.visied_locations.add(self.current_location)


