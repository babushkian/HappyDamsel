from pathlib import Path
from typing import Protocol
import yaml
from damsel.model.content import RawContent


class Loader(Protocol):
    @classmethod
    def load(cls) -> RawContent: ...


class YamlLoader:
    DATA_DIR = Path(__file__).resolve().parents[2] / "data"

    @classmethod
    def load(cls) -> RawContent:
        items = cls._load_yaml("items.yaml")
        choices = cls._load_yaml("choices.yaml").get("choices", {})

        locations: dict = {}
        for path in (cls.DATA_DIR / "locations").glob("*.yaml"):
            locations[path.stem] = cls._load_yaml(f"locations/{path.name}")

        objects: dict = {}
        for path in (cls.DATA_DIR / "objects").glob("*.yaml"):
            objects.update(cls._load_yaml(f"objects/{path.name}"))

        return RawContent(items=items, locations=locations, objects=objects, choices=choices)

    @classmethod
    def _load_yaml(cls, relative: str) -> dict:
        with (cls.DATA_DIR / relative).open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
