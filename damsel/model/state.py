from dataclasses import dataclass, field
from damsel.model.types import ItemId, ObjectId, LocationId


@dataclass
class ObjectState:
    is_open: bool = False
    is_locked: bool = False
    is_on: bool = False
    items: list[ItemId] = field(default_factory=list)


@dataclass
class GameState:
    current_location: LocationId
    return_location: LocationId | None = None
    locations_items: dict[LocationId, list[ItemId]] = field(default_factory=dict)
    objects: dict[ObjectId, ObjectState] = field(default_factory=dict)
    visited_locations: set[LocationId] = field(default_factory=set)
    flags: dict[str, bool] = field(default_factory=dict)

    def set_location_visited(self) -> None:
        self.visited_locations.add(self.current_location)
