from content_parts import GameContent
from definitions import Choice, Result
from effects import EFFECTS
from definitions import GameState
from content_parts import GameContent

class GenericChoices:
    def __init__(self, state: GameState, content: GameContent):
        self.state = state
        self.content = content

    def pickup(self) -> list[Choice]:
        pickup_options: list[Choice] = []
        for iid in self.state.locations_items[self.state.current_location]:
            item = self.content.items[iid]
            pickup_options.append(
                Choice(
                    id=f"pick_up_{iid}",
                    text=f"Взять {item.name}",
                    result=Result("generic_pickup", {"item": iid}),
                    do=[EFFECTS["get_item"]({"item": iid})]
                )
            )
        return sorted(pickup_options, key=lambda i: i.text)

    def open(self) -> list[Choice]:
        choices: list[Choice] = []
        for fid in self.content.locations[self.state.current_location].objects:
            furniture = self.content.furniture[fid]
            if furniture.can_open:
                if not (self.state.objects[fid].flags["open"]  or self.state.objects[fid].flags["locked"]):
                   choices.append(
                       Choice(
                           id=f"open_{fid}",
                           text=f"Открыть {furniture.name}",
                           result=Result("generic_open", {"object": fid}),
                           do=[EFFECTS["open_object"]({"object": fid})]

                       )
                   )
        return choices

