from dataclasses import dataclass, field
from definitions import ItemId, LocationId, LocationDef, Inventory, Choice, ItemDef, FurnitureDef, ObjectId


@dataclass(frozen=True)
class RawContent:
    items: dict = field(default_factory=dict)
    locations: dict= field(default_factory=dict)
    inventory: dict = field(default_factory=dict)
    choices: dict = field(default_factory=dict)


@dataclass(frozen=True)
class GameContent:
    items: dict[ItemId, ItemDef]
    furniture: dict[ObjectId, FurnitureDef]
    locations: dict[LocationId, LocationDef]
    choices: dict[str, Choice]