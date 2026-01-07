from dataclasses import dataclass, field
from definitions import ItemId, Item, LocationId, Location, Inventory, Choice


@dataclass(frozen=True)
class RawContent:
    items: dict = field(default_factory=dict)
    locations: dict = field(default_factory=dict)
    inventory: dict = field(default_factory=dict)
    choices: dict = field(default_factory=dict)


@dataclass(frozen=True)
class GameContent:
    items: dict[ItemId, Item]
    locations: dict[LocationId, Location]
    inventory: Inventory
    choices: dict[str, Choice]