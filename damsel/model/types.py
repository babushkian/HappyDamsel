from typing import Callable, NewType, TYPE_CHECKING

if TYPE_CHECKING:
    from damsel.model.state import GameState
    from damsel.model.content import GameContent

ItemId = NewType("ItemId", str)
ObjectId = NewType("ObjectId", str)
LocationId = NewType("LocationId", str)
NpcId = NewType("NpcId", str)
# Идентификатор действия непрозрачен для фронтендов: он возвращается в dispatch()
# как есть, его нельзя парсить или конструировать на стороне клиента.
ActionId = NewType("ActionId", str)

INVENTORY_LOCATION_ID = LocationId("inventory")

Condition = Callable[["GameState", "GameContent"], bool]
Effect = Callable[["GameState", "GameContent"], None]
