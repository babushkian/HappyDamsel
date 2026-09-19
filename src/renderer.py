from dataclasses import dataclass
from definitions import GameState, Choice, INVENTORY_LOCATION_ID
from content_parts import GameContent


@dataclass
class GameRenderer:
    state: GameState
    content: GameContent

    def render_location(self, verbose: bool = False) -> str:
        location = self.content.locations[self.state.current_location]
        description = f"{location.name}\n{location.description}\n" if verbose else f"{location.name}\n"

        for fid in location.objects:
            furn = self.content.furniture[fid]
            obj = self.state.objects[fid]
            if furn.kind == "container":
                status = "(заперто)" if obj.flags["locked"] else ("(закрыто)" if not obj.flags["open"] else "")
                if verbose:
                    description += f"{furn.name} {status}. {furn.description}\n"
                else:
                    description += f"{furn.name} {status}\n"
            elif furn.kind == "door":
                status = "(открыто)" if obj.flags["open"] else "(закрыто)"
                description += f"{furn.name}{status}. {furn.description}\n"
            elif furn.kind == "switch":
                status = "(включено)" if obj.flags["turned_on"] else "(выключено)"
                description += f"{furn.name}{status}. {furn.description}\n"

        floor_items = [self.content.items[iid].name for iid in self.state.locations_items[self.state.current_location]]
        if floor_items:
            description += f"Здесь находится: {', '.join(floor_items)}\n"

        inventory = [self.content.items[iid].name for iid in self.state.locations_items[INVENTORY_LOCATION_ID]]
        if inventory:
            description += f"В инвентаре: {', '.join(inventory)}\n"

        return description

    def render_choices(self, choices_dict: dict[str, Choice]) -> str:
        return "".join(f"{n}. {c.text}\n" for n, c in choices_dict.items())
