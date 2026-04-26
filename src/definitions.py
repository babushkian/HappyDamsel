from typing import Callable, Self, NewType, TYPE_CHECKING
from dataclasses import dataclass, field

from renderers import render_template

if TYPE_CHECKING:
    from content_parts import GameContent

ItemId = NewType("ItemId", str)
ObjectId = NewType("ObjectId", str)
LocationId = NewType("LocationId", str)


INVENTORY_LOCATION_ID = LocationId("inventory")

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
    link_to: ObjectId | None = None


Condition = Callable[["GameState", "GameContent"], bool]
Effect = Callable[["GameState", "GameContent"], None]


@dataclass(frozen=True)
class ExitDef:
    target: LocationId
    text: str                     # "Пойти на кухню"
    when: list[Condition] = field(default_factory=list)
    do: list[Effect] = field(default_factory=list)


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
class Result:
    template: str
    params: dict[str, str] = field(default_factory=dict)

@dataclass
class Choice:
    id: str
    text: str
    when: list[Condition] = field(default_factory=list)
    do: list[Effect] = field(default_factory=list)
    result_text: str | None = None
    result: Result | None = None

    def is_available(self, state: "GameState", content: "GameContent") -> bool:
        return all(cond(state, content) for cond in self.when)

    def apply(self, state: "GameState", content: "GameContent") -> str:
        if not self.is_available(state, content):
            raise RuntimeError("Conditions not met")
        for effect in self.do:
            effect(state, content)

        if self.result_text is not None:
            return self.result_text
        if self.result is not None:
            return render_template(self.result, content)
        return ""


@dataclass
class GameState:
    current_location: LocationId
    return_location: LocationId | None = None
    locations_items: dict[LocationId, list[ItemId]] = field(default_factory=dict)
    objects: dict[ObjectId, ObjectState] = field(default_factory=dict)
    visited_locations: set[LocationId] = field(default_factory=set)
    flags: dict[str, bool] = field(default_factory=dict,)


    def set_location_visited(self) -> None:
        if self.current_location not in self.visited_locations:
            self.visited_locations.add(self.current_location)


