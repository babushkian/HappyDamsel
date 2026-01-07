from pathlib import Path
from typing import Protocol
import yaml
from content_parts import RawContent

class Loader(Protocol):
    @classmethod
    def load(cls) -> RawContent: ...


class YamlLoader(Loader):
    CONTENT_DIR = Path(__file__).resolve().parent / "world"

    @classmethod
    def load(cls):
        with (cls.CONTENT_DIR / "items.yaml").open(mode="r", encoding="utf-8") as file:
            raw_item_data = yaml.safe_load(file.read())
        with (cls.CONTENT_DIR / "locations.yaml").open(mode="r", encoding="utf-8") as file:
            raw_location_data = yaml.safe_load(file.read())
        with (cls.CONTENT_DIR / "inventory.yaml").open(mode="r", encoding="utf-8") as file:
            raw_inventory_data = yaml.safe_load(file.read())
        with (cls.CONTENT_DIR / "choices.yaml").open(mode="r", encoding="utf-8") as file:
            yaml_choices = yaml.safe_load(file.read())
        raw_choices = {}
        for cid, raw in yaml_choices["choices"].items():
            raw_choices[cid] = raw

        return RawContent(
            items=raw_item_data,
            locations=raw_location_data,
            inventory=raw_inventory_data,
            choices=raw_choices
        )