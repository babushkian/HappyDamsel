
import yaml
from pathlib import Path
from pprint import pprint
from conditions import CONDITIONS
from effects import EFFECTS
from definitions import (ItemId, Item,
                         LocationId, Location,
                         ObjectId, Container,
                         Choice,
                         Condition,
                         Effect,
                         Inventory,
                         GameState,

                         )

CONTENT_DIR = Path(__file__).resolve().parent / "world"


ITEMS: dict[ItemId, Item] = {}
LOCATIONS: dict[LocationId, Location] = {}
CHOICES_RAW: dict[str, dict] = {}
INVENTORY = Inventory(items={})




def build_item(iid: str,  data: dict):
    item_id = ItemId(iid)
    ITEMS[item_id] = Item(
            id=item_id,
            name=data["name"],
            description=data["description"],
            consumable=data["consumable"],
        )


def build_location( lid: str,  data: dict):
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
            locked=cont_data["locked"],
            open=cont_data["open"],
            contents=[ItemId(iid) for iid in cont_data.get("contents", [])]
        )
    loc.containers = containers
    LOCATIONS[location_id] = loc



def build_inventory(data: dict):
    invtry: dict[ItemId, int]
    for item in data["items"].items():
        item_id = ItemId(item["item"])
        invtry[item_id] = item["qty"]
    INVENTORY.items = invtry


CHOICES: dict[str, Choice]={}

def build_choice(cid: str,  data: dict):
    conditions: list[Condition] = []
    for c in data.get("conditions", []):
        conditions.append( CONDITIONS[c["type"]](c))
    effects: list[Effect] = []
    for e in data.get("effects", []):
        effects.append( EFFECTS[e["type"]](e))
    CHOICES[cid] = Choice(
        id=cid,
        text=data["text"],
        when=conditions,
        do=effects
    )

# первая фаза загрузки (сырые данны данные)
with (CONTENT_DIR / "items.yaml").open(mode="r", encoding="utf-8") as file:
    raw_item_data = yaml.safe_load(file.read())
with (CONTENT_DIR / "locations.yaml").open(mode="r", encoding="utf-8") as file:
    raw_location_data = yaml.safe_load(file.read())
with (CONTENT_DIR / "inventory.yaml").open(mode="r", encoding="utf-8") as file:
    raw_inventory_data = yaml.safe_load(file.read())
with (CONTENT_DIR / "choices.yaml").open(mode="r", encoding="utf-8") as file:
    yaml_choices = yaml.safe_load(file.read())

def load_choices_raw(data: dict):
    for cid, raw in data["choices"].items():
        CHOICES_RAW[cid] = raw

load_choices_raw(yaml_choices)

# вторая фаза загрузки (создаем объекты на основе данных)
for  iid, raw in raw_item_data.items():
    build_item(iid, raw)

for  lid, raw in raw_location_data.items():
    build_location(lid, raw)

for  cid, struct in CHOICES_RAW.items():
    build_choice(cid, struct)
