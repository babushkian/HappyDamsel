from content_parts import GameContent
from loaders import Loader
from conditions import CONDITIONS
from effects import EFFECTS
from definitions import (ItemId,
                         LocationId,
                         ObjectId,
                         Choice,
                         Condition,
                         Effect,
                         Inventory, ItemDef, LocationDef, FurnitureDef,
                         GameState, ObjectState
                         )



class ContentLoader:


    def __init__(self, loader: Loader) -> None:
        self.ITEMS: dict[ItemId, ItemDef] = {}
        self.LOCATIONS: dict[LocationId, LocationDef] = {}
        self.INVENTORY = Inventory(items={})
        self.CHOICES: dict[str, Choice] = {}
        self.FURNITURE: dict[ObjectId, FurnitureDef] = {}
        self.raw_content = loader.load()
        self.object_states: dict[ObjectId, ObjectState] = {}

        self.location_items: dict[LocationId, list[ItemId]]= {}


    def init_content(self) -> tuple[GameContent, GameState]:
        for iid, raw in self.raw_content.items.items():
            self.build_item(iid, raw)

        for lid, raw in self.raw_content.locations.items():
            self.build_location(lid, raw)

        self.build_inventory(self.raw_content.inventory["items"])

        for cid, struct in self.raw_content.choices.items():
            print(struct)
            self.build_choice(cid, struct)


        print(self.location_items)
        print(self.object_states)
        content = GameContent(
            items=self.ITEMS,
            furniture=self.FURNITURE,
            locations=self.LOCATIONS,
            choices=self.CHOICES
        )
        state = GameState(
            current_location=LocationId("attic"),
            inventory=self.INVENTORY,
            locations_items=self.location_items,
            objects=self.object_states,
            flags={},
        )
        return content, state


    def build_item(self, iid: str,  data: dict):
        item_id = ItemId(iid)
        self.ITEMS[item_id] = ItemDef(
                id=item_id,
                name=data["name"],
                description=data["description"],
                consumable=data["consumable"],
            )



    def build_location(self, lid: str,  data: dict):
        location_id = LocationId(lid)

        raw_items = data.get("items", [])
        self.location_items[location_id] = [ItemId(iid) for iid in raw_items]

        objects: list[ObjectId] = []
        for fid, furn_data in data.get("furniture", {}).items():
            obj_id = ObjectId(fid)
            self.FURNITURE[obj_id] = FurnitureDef(
                id=obj_id,
                kind=furn_data["kind"],
                name=furn_data["name"],
                description=furn_data["description"],
                is_container=furn_data.get("is_container", False),
                can_lock=furn_data.get("can_lock", False),
                can_open=furn_data.get("can_open", False),
                is_transparent=furn_data.get("is_transparent", False),
            )
            objects.append(obj_id)
            self.object_states[obj_id] = ObjectState(
                    flags={"locked": furn_data.get("locked", False), "open": furn_data.get("open", True)},
                    items=[ItemId(iid) for iid in furn_data.get("contents", [])],
            )
        loc = LocationDef(
            id=location_id,
            name=data["name"],
            description=data["description"],
            objects=objects,
            items=self.location_items[location_id]
        )



        self.LOCATIONS[location_id] = loc



    def build_inventory(self, data: list[dict]):
        invtry: dict[ItemId, int] = {}
        for item in data:
            item_id = ItemId(item["item"])
            invtry[item_id] = item["qty"]
        self.INVENTORY.items = invtry


    def build_choice(self, cid: str,  data: dict):
        conditions: list[Condition] = []
        for c in data.get("conditions", []):
            conditions.append( CONDITIONS[c["type"]](c))
        effects: list[Effect] = []
        for e in data.get("effects", []):
            effects.append( EFFECTS[e["type"]](e))
        self.CHOICES[cid] = Choice(
            id=cid,
            text=data["text"],
            result_text=data.get("result_text", None),
            result_renderer=data.get("result_renderer", None),
            when=conditions,
            do=effects
        )

