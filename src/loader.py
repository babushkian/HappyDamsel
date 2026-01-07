
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

def load_choices_raw(data: dict):
    for cid, raw in data["choices"].items():
        CHOICES_RAW[cid] = raw

content_file =CONTENT_DIR / "choices.yaml"
with content_file.open(mode="r", encoding="utf-8") as file:
    yaml_choices = yaml.safe_load(file.read())
load_choices_raw(yaml_choices)

with (CONTENT_DIR / "items.yaml").open(mode="r", encoding="utf-8") as file:
    raw_item_data = yaml.safe_load(file.read())
with (CONTENT_DIR / "locations.yaml").open(mode="r", encoding="utf-8") as file:
    raw_location_data = yaml.safe_load(file.read())




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

for  iid, raw in raw_item_data.items():
    build_item(iid, raw)

for  lid, raw in raw_location_data.items():
    build_location(lid, raw)

pprint(ITEMS)
# инвентарь с ключом
inventory = Inventory(items={ItemId("rusty_key"): 1})

# состояние игры
state = GameState(
    current_location=LocationId("attic"),
    locations=LOCATIONS,
    inventory=inventory,
    flags={},
)


CHOICES: dict[str, Choice]={}

def build_choice(state: GameState, cid: str,  data: dict):
    conditions: list[Condition] = []
    for c in data.get("conditions", []):
        conditions.append( CONDITIONS[c["type"]](state, c))
    effects: list[Effect] = []
    for e in data.get("effects", []):
        effects.append( EFFECTS[e["type"]](state, e))
    CHOICES[cid] = Choice(
        id=cid,
        text=data["text"],
        when=conditions,
        do=effects
    )

for  cid, struct in CHOICES_RAW.items():
    build_choice(state, cid, struct)
