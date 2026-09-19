from damsel.model.content import Choice, Result, GameContent
from damsel.model.state import GameState
from damsel.model.types import INVENTORY_LOCATION_ID
from damsel.actions.effects import EFFECTS


class GenericChoices:
    def __init__(self, state: GameState, content: GameContent) -> None:
        self.state = state
        self.content = content

    def pickup(self) -> list[Choice]:
        options = []
        for iid in self.state.locations_items[self.state.current_location]:
            item = self.content.items[iid]
            options.append(Choice(
                id=f"pick_up_{iid}",
                text=f"Взять {item.name}",
                result=Result("generic_pickup", {"item": iid}),
                do=[EFFECTS["get_item"]({"item": iid})],
            ))
        return sorted(options, key=lambda c: c.text)

    def drop(self) -> list[Choice]:
        options = []
        for iid in self.state.locations_items[INVENTORY_LOCATION_ID]:
            item = self.content.items[iid]
            options.append(Choice(
                id=f"drop_{iid}",
                text=f"Бросить {item.name}",
                result=Result("generic_drop", {"item": iid}),
                do=[EFFECTS["drop_item"]({"item": iid})],
            ))
        return sorted(options, key=lambda c: c.text)

    def open(self) -> list[Choice]:
        options = []
        for fid in self.content.locations[self.state.current_location].objects:
            furn = self.content.furniture[fid]
            obj = self.state.objects[fid]
            if furn.can_open and not obj.flags["open"] and not obj.flags["locked"]:
                options.append(Choice(
                    id=f"open_{fid}",
                    text=f"Открыть {furn.name}",
                    result=Result("generic_open", {"object": fid}),
                    do=[EFFECTS["open_object"]({"object": fid})],
                ))
        return options

    def close(self) -> list[Choice]:
        options = []
        for fid in self.content.locations[self.state.current_location].objects:
            furn = self.content.furniture[fid]
            obj = self.state.objects[fid]
            if furn.can_open and obj.flags["open"] and not obj.flags["locked"]:
                options.append(Choice(
                    id=f"close_{fid}",
                    text=f"Закрыть {furn.name}",
                    result=Result("generic_close", {"object": fid}),
                    do=[EFFECTS["close_object"]({"object": fid})],
                ))
        return options
