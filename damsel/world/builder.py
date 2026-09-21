from typing import Any

from damsel.actions.conditions import CONDITIONS
from damsel.actions.effects import EFFECTS
from damsel.model.content import (
    GameContent,
    ItemDef,
    FurnitureDef,
    LocationDef,
    Choice,
    ObjectOverride,
    Result,
    ObjectKind,
    ChoiceScope,
)
from damsel.model.state import GameState, ObjectState
from damsel.model.text import ConditionalText, Text
from damsel.model.types import ItemId, ObjectId, LocationId, Condition, Effect
from damsel.world.loader import Loader


def _build_text(data: Any) -> Text:
    """YAML: простая строка ИЛИ список вариантов с условиями.

    Варианты:
        description: "текст"
        descriptions:
          - when: [{type: ..., ...}]
            text: "текст"
          - default: "текст"
    """
    if isinstance(data, str):
        return data
    raise ValueError(f"Ожидался текст, получено: {data!r}")


def _build_variants(raw: list[Any]) -> ConditionalText:
    variants: list[tuple[list[Condition], str]] = []
    default: str | None = None
    for entry in raw:
        if "default" in entry:
            default = entry["default"]
            continue
        variants.append((_build_conditions(entry.get("when", [])), entry["text"]))
    return ConditionalText(variants=variants, default=default)


def _build_conditions(raw: list[Any]) -> list[Condition]:
    return [CONDITIONS[c["type"]](c) for c in raw]


def _build_effects(raw: list[Any]) -> list[Effect]:
    return [EFFECTS[e["type"]](e) for e in raw]


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

    def _build_item(self, iid: str, data: dict[str, Any]) -> None:
        item_id = ItemId(iid)
        description = _build_description(data)
        self._items[item_id] = ItemDef(
            id=item_id,
            name=data["name"],
            description=description,
            consumable=data["consumable"],
        )

    def _build_furniture(self, oid: str, data: dict[str, Any]) -> None:
        obj_id = ObjectId(oid)
        self._furniture[obj_id] = FurnitureDef(
            id=obj_id,
            kind=ObjectKind(data["kind"]),
            name=data["name"],
            description=_build_description(data),
            is_container=data.get("is_container", False),
            can_lock=data.get("can_lock", False),
            can_open=data.get("can_open", False),
            is_transparent=data.get("is_transparent", False),
            turnable=data.get("turnable", False),
            visible_when=_build_conditions(data.get("visible_when", [])),
            contents_visible_when=_build_conditions(data.get("contents_visible_when", [])),
        )
        self._object_states[obj_id] = ObjectState(
            is_locked=data.get("locked", False),
            is_open=data.get("open", True),
            is_on=data.get("turned_on", False),
            items=[ItemId(iid) for iid in data.get("contents", []) if iid],
        )

    def _build_location(self, lid: str, data: dict[str, Any]) -> None:
        location_id = LocationId(lid)
        raw_items = data.get("items", [])
        self._location_items[location_id] = [ItemId(iid) for iid in raw_items if iid]
        overrides = {
            ObjectId(oid): ObjectOverride(
                name=ov.get("name"),
                description=(
                    _build_variants(ov["descriptions"])
                    if "descriptions" in ov
                    else ov.get("description")
                ),
            )
            for oid, ov in data.get("object_overrides", {}).items()
        }
        self._locations[location_id] = LocationDef(
            id=location_id,
            name=data["name"],
            description=_build_description(data),
            objects=[ObjectId(oid) for oid in data.get("objects", [])],
            lit_when=_build_conditions(data.get("lit_when", [])),
            object_overrides=overrides,
            items=self._location_items[location_id],
        )

    def _build_choice(self, cid: str, data: dict[str, Any]) -> None:
        conditions = _build_conditions(data.get("conditions", []))
        effects = _build_effects(data.get("effects", []))

        result = None
        if data.get("result"):
            result = Result(
                template=data["result"]["template"],
                params=data["result"].get("params", {}),
            )

        result_text: Text | None = None
        if "result_texts" in data:
            result_text = _build_variants(data["result_texts"])
        elif data.get("result_text") is not None:
            result_text = data["result_text"]

        self._choices[cid] = Choice(
            id=cid,
            text=data["text"],
            result_text=result_text,
            result=result,
            when=conditions,
            do=effects,
            scope=ChoiceScope(data.get("scope", ChoiceScope.LOCATION)),
        )


def _build_description(data: dict[str, Any]) -> Text:
    """description: str | descriptions: [варианты]. Варианты имеют приоритет."""
    if "descriptions" in data:
        return _build_variants(data["descriptions"])
    return _build_text(data["description"])
