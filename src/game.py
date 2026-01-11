from pprint import pprint
from dataclasses import dataclass
from effects import EFFECTS
from content_parts import GameContent
from init_content import ContentLoader
from loaders import YamlLoader
from definitions import  LocationId, GameState, Choice


cl = ContentLoader(YamlLoader)
content = cl.init_content()
del cl

# состояние игры
state = GameState(
    current_location=LocationId("attic"),
    locations=content.locations,
    inventory=content.inventory,
    flags={},
)

@dataclass
class GameRenderer:
    state: GameState
    content: GameContent

    def render_location(self, verbose: bool = False):
        description = ""
        loc = self.state.location()
        if not loc:
            raise ValueError(f"Локация не найдена")
        description += loc.describe(verbose) + "\n"

        for c in loc.containers.keys():
            container = self.state.get_container(c)
            description += container.describe(verbose) + "\n"
        if loc.items:
            item_names: list[str] = []
            for iid in loc.items:
                item_names.append(self.content.items[iid].describe(verbose))
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
        loc = self.state.location()
        verbose = not loc.visited
        loc.set_visited()
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
            if c.is_available(self.state):
                choices.append(c)
        choices.extend(self.generate_pickup_choices_for_location())
        return choices


    def generate_pickup_choices_for_location(self) -> list[Choice]:
        loc = self.state.location()
        pickup_options: list[Choice] = []
        if loc:
            for iid in loc.items:
                item = self.content.items[iid]
                pickup_options.append(
                    Choice(
                        id=f"pick_up_{iid.value}",
                        text=f"Взять {item.name}",
                        description =f"Ты взял {item.name}",
                        do=[EFFECTS["get_item"]({"item": iid.value})]
                    )
                )

        return sorted(pickup_options, key=lambda i: i.text)


    def process(self, associations: dict[str, Choice]):
        self.previous_tick_location = self.state.current_location
        available_options = list(associations)
        while True:
            option = input(">")
            if  option not in available_options:
                print("Неверная опция!")
                continue
            action_description = associations[option].apply(self.state)
            print(action_description)
            break

gr = GameRenderer(state, content)
game = Game(state, content, gr)
game.run()
