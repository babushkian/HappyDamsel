from content_parts import GameContent
from loaders import Loader
from conditions import CONDITIONS
from effects import EFFECTS
from definitions import (ItemId, Item,
                         LocationId, Location,
                         ObjectId, Container,
                         Choice,
                         Condition,
                         Effect,
                         Inventory,
                         )



class ContentLoader:


    def __init__(self, loader: Loader) -> None:
        self.ITEMS: dict[ItemId, Item] = {}
        self.LOCATIONS: dict[LocationId, Location] = {}
        self.INVENTORY = Inventory(items={})
        self.CHOICES: dict[str, Choice] = {}
        self.raw_content = loader.load()




    def init_content(self) -> GameContent:
        for iid, raw in self.raw_content.items.items():
            self.build_item(iid, raw)

        for lid, raw in self.raw_content.locations.items():
            self.build_location(lid, raw)

        self.build_inventory(self.raw_content.inventory["items"])

        for cid, struct in self.raw_content.choices.items():
            self.build_choice(cid, struct)

        return GameContent(
            items=self.ITEMS,
            locations=self.LOCATIONS,
            inventory=self.INVENTORY,
            choices=self.CHOICES
        )


    def build_item(self, iid: str,  data: dict):
        item_id = ItemId(iid)
        self.ITEMS[item_id] = Item(
                id=item_id,
                name=data["name"],
                description=data["description"],
                consumable=data["consumable"],
            )



    def build_location(self, lid: str,  data: dict):
        location_id = LocationId(lid)
        loc = Location(
            id=location_id,
            name=data["name"],
            description=data["description"],
            containers={},
        )
        containers:dict[ObjectId, Container] = {}
        for cid, cont_data in data.get("containers", {}).items():
            container_id = ObjectId(cid)
            containers[container_id] = Container(
                id=container_id,
                name=cont_data["name"],
                description=cont_data["description"],
                locked=cont_data["locked"],
                open=cont_data["open"],
                contents=[ItemId(iid) for iid in cont_data.get("contents", [])]
            )
        loc.containers = containers
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
            when=conditions,
            do=effects
        )

