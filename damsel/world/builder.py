from damsel.model.content import (
    GameContent, RawContent,
    ItemDef, FurnitureDef, LocationDef, Choice, Result,
    ObjectKind, ChoiceScope,
)
from damsel.model.state import GameState, ObjectState
from damsel.model.types import ItemId, ObjectId, LocationId, Condition, Effect, INVENTORY_LOCATION_ID
from damsel.world.loader import Loader


class ContentBuilder:

    def __init__(self, loader: Loader) -> None:
        self._raw = loader.load()
        self._items: dict[ItemId, ItemDef] = {}
        self._furniture: dict[ObjectId, FurnitureDef] = {}
        self._locations: dict[LocationId, LocationDef] = {}
        self._choices: dict[str, Choice] = {}
        self._object_states: dict[ObjectId, ObjectState] = {}
        self._location_items: dict[LocationId, list[ItemId]] = {}

    def build(self) -> tuple[GameContent, GameState]:
        for iid, raw in self._raw.items.items():
            self._build_item(iid, raw)

        for oid, raw in self._raw.objects.items():
            self._build_furniture(oid, raw)

        for lid, raw in self._raw.locations.items():
            self._build_location(lid, raw)

        for cid, raw in self._raw.choices.items():
            self._build_choice(cid, raw)

        content = GameContent(
            items=self._items,
            furniture=self._furniture,
            locations=self._locations,
            choices=self._choices,
        )
        state = GameState(
            current_location=LocationId("attic"),
            locations_items=self._location_items,
            objects=self._object_states,
        )
        return content, state

    def _build_item(self, iid: str, data: dict) -> None:
        item_id = ItemId(iid)
        self._items[item_id] = ItemDef(
            id=item_id,
            name=data["name"],
            description=data["description"],
            consumable=data["consumable"],
        )

    def _build_furniture(self, oid: str, data: dict) -> None:
        obj_id = ObjectId(oid)
        self._furniture[obj_id] = FurnitureDef(
            id=obj_id,
            kind=ObjectKind(data["kind"]),
            name=data["name"],
            description=data["description"],
            is_container=data.get("is_container", False),
            can_lock=data.get("can_lock", False),
            can_open=data.get("can_open", False),
            is_transparent=data.get("is_transparent", False),
            turnable=data.get("turnable", False),
            link_to=ObjectId(data["link_to"]) if data.get("link_to") else None,
        )
        self._object_states[obj_id] = ObjectState(
            is_locked=data.get("locked", False),
            is_open=data.get("open", True),
            is_on=data.get("turned_on", False),
            items=[ItemId(iid) for iid in data.get("contents", []) if iid],
        )

    def _build_location(self, lid: str, data: dict) -> None:
        location_id = LocationId(lid)
        raw_items = data.get("items", [])
        self._location_items[location_id] = [ItemId(iid) for iid in raw_items if iid]
        self._locations[location_id] = LocationDef(
            id=location_id,
            name=data["name"],
            description=data["description"],
            objects=[ObjectId(oid) for oid in data.get("objects", [])],
            items=self._location_items[location_id],
        )

    def _build_choice(self, cid: str, data: dict) -> None:
        from damsel.actions.conditions import CONDITIONS
        from damsel.actions.effects import EFFECTS

        conditions: list[Condition] = [CONDITIONS[c["type"]](c) for c in data.get("conditions", [])]
        effects: list[Effect] = [EFFECTS[e["type"]](e) for e in data.get("effects", [])]

        result = None
        if data.get("result"):
            result = Result(
                template=data["result"]["template"],
                params=data["result"].get("params", {}),
            )

        self._choices[cid] = Choice(
            id=cid,
            text=data["text"],
            result_text=data.get("result_text"),
            result=result,
            when=conditions,
            do=effects,
            scope=ChoiceScope(data.get("scope", ChoiceScope.LOCATION)),
        )
