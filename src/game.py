from pprint import pprint
from dataclasses import dataclass
from effects import EFFECTS
from content_parts import GameContent
from init_content import ContentLoader
from loaders import YamlLoader
from definitions import LocationId, GameState, Choice, Result
from choices import GenericChoices


cl = ContentLoader(YamlLoader)
content, state = cl.init_content()
for c in content.choices.values():
    print(c)
del cl

for f in content.furniture.values():
    print(f)
# состояние игры

gc = GenericChoices(state, content)

@dataclass
class GameRenderer:
    state: GameState
    content: GameContent

    def render_location(self, verbose: bool = False):
        description = ""
        location = self.content.locations[self.state.current_location]
        if verbose:
            description += f"{location.name}\n{location.description}"
        else:
            description += location.name
        description += "\n"

        furniture = location.objects
        print(furniture)
        for fid in furniture:
            furn_def = self.content.furniture[fid]
            if furn_def.kind == "container":
                fs = self.state.objects[fid]
                status = "(закрыто)" if not fs.flags["open"] else ""
                status = "(заперто)" if fs.flags["locked"] else status
                if verbose:
                    description += f"{furn_def.name} {status}. {furn_def.description}"
                else:
                    description +=f"{furn_def.name} {status}"
                description += "\n"
            if furn_def.kind == "door":
                status = "(закрыто)" if not self.state.objects[fid].flags["open"] else "(открыто)"
                description += f"{furn_def.name}{status}. {furn_def.description}'\n"
            if furn_def.kind == "switch":
                status = "(включено)" if self.state.objects[fid].flags["turned_on"] else "(выключено)"
                description += f"{furn_def.name}{status}. {furn_def.description}\n"

        item_names: list[str] = []
        for iid in self.state.locations_items[self.state.current_location]:
            item_names.append(self.content.items[iid].name)
        if item_names:
            description += f"Здесь находится: {"\n".join(item_names)}\n"
        return description



    def render_choices(self, choices_dict: dict[str, Choice]) -> str:
        description = ""
        for n, c in  choices_dict.items():
            description +=f"{n}. {c.text}\n"
        return description



@dataclass
class Game:
    state: GameState
    content: GameContent
    renderer: GameRenderer
    time: int = 0
    previous_tick_location: LocationId | None = None

    def run(self) -> None:
        while self.time < 10:
            self.tick()


    def tick(self) -> None:
        self.time += 1
        verbose = self.state.current_location not in self.state.visited_locations


        choices = self.get_available_choices()
        choices_dict = {str(n): c for n, c in enumerate(choices, 1)}
        choice_description = self.renderer.render_choices(choices_dict)
        
        # Печатаем описание локации только при первом посещении или смене локации
        if verbose or self.state.current_location != self.previous_tick_location:
            location_description = self.renderer.render_location(verbose)
            print(location_description)
            
        print(choice_description)
        self.process(choices_dict)


    def get_available_choices(self) -> list[Choice]:
        choices: list[Choice] = []
        for c in self.content.choices.values():
            if c.is_available(self.state, self.content):
                choices.append(c)
        choices.extend(gc.pickup())
        choices.extend(gc.open())
        return choices





    def process(self, associations: dict[str, Choice]):
        self.previous_tick_location = self.state.current_location
        available_options = list(associations)
        while True:
            option = input(">")
            if  option not in available_options:
                print("Неверная опция!")
                continue
            action_description = associations[option].apply(self.state, self.content)
            print(action_description)
            break

gr = GameRenderer(state, content)
game = Game(state, content, gr)
game.run()
