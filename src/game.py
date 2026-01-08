from pprint import pprint
from dataclasses import dataclass
from effects import EFFECTS
from content_parts import GameContent
from init_content import ContentLoader
from loaders import YamlLoader
from definitions import ItemId, ObjectId, LocationId, GameState, Inventory, Choice
from itertools import chain


# идентификаторы
RUSTY_KEY = ItemId("rusty_key")
# GOLD_RING = ItemId("gold_ring")
BOX = ObjectId("wooden_box")
# CHEST = ObjectId("iron_chest")
ATTIC = LocationId("attic")
# HALL = LocationId("hall")

cl = ContentLoader(YamlLoader)

content = cl.init_content()
del cl

# состояние игры
state = GameState(
    current_location=ATTIC,
    locations=content.locations,
    inventory=content.inventory,
    flags={},
)

@dataclass
class Game:
    state: GameState
    content: GameContent
    time: int = 0

    def run(self):
        while self.time < 10:
            self.tick()


    def tick(self):
        self.time += 1
        self.render_scene()
        dynamic_choices = self.create_choices()
        choices = self.render_choices(dynamic_choices)
        self.process(choices)

    def render_scene(self):
        loc = self.state.location()
        print(loc.name)
        print(loc.description)
        for c in loc.containers:
            container = self.state.get_container(c)
            print(container.description)
        if loc.items:
            item_names: list[str] = []
            for iid in loc.items:
                item_names.append(self.content.items[iid].name.lower())
            print(f"Здесь находится: {", ".join(item_names)}")


    def create_choices(self) -> list[Choice]:
        return self.create_pickup_choices()

    def create_pickup_choices(self) -> list[Choice]:
        loc = self.state.location()
        pickup_options: list[Choice] = []
        if loc:
            for iid in loc.items:
                item = self.content.items[iid]
                pickup_options.append(
                    Choice(
                        id=f"{self.state.current_location.value}_get_{iid.value}",
                        text=f"Взять {item.name}",
                        description =f"Ты взял {item.name}",
                        do=[EFFECTS["get_item"]({"item": iid.value})]
                    )
                )

        return sorted(pickup_options, key=lambda i: i.text)

    def render_choices(self, dynamic_choices) -> dict[str, Choice]:
        counter = 1
        option_associations: dict[str, Choice] = {}
        for c in chain(self.content.choices.values(), dynamic_choices):
            if c.is_available(self.state):
                option_associations[str(counter)] = c
                print(f"{counter}. {c.text}")
                counter += 1
        return option_associations

    def process(self, associations):
        available_options = list(associations)
        while True:
            option = input(">")
            if  option not in available_options:
                print("Неверная опция!")
                continue
            action_description = associations[option].apply(self.state)
            print(action_description)
            break


game = Game(state, content)
game.run()
