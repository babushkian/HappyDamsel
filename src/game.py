from pprint import pprint
from dataclasses import dataclass
from init_content import ContentLoader
from loaders import YamlLoader
from definitions import ItemId, ObjectId, LocationId, GameState, Inventory, Choice

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
    time: int = 0

    def run(self):
        while self.time < 10:
            self.tick()


    def tick(self):
        self.time += 1
        self.render_scene()
        choices = self.render_choices()
        self.process(choices)

    def render_scene(self):
        loc = self.state.location()
        print(loc.name)
        print(loc.description)
        for c in loc.containers:
            container = self.state.get_container(c)
            print(container.description)
        if loc.items:
            for iid in loc.items:
                item_names: list[str] = []
                item_names.append(content.items[iid].name.lower())

            print(f"Здесь находится: {", ".join(item_names)}")



    def render_choices(self):
        counter = 1
        option_associations: dict[str, Choice] = {}
        for c in content.choices.values():
            if c.is_available(self.state):
                option_associations[str(counter)] = c.id
                print(f"{counter}. {c.text}")
                counter += 1
        return option_associations

    def process(self, associations):
        available_options = list(associations)
        while True:
            option = input(">")
            if  option not in available_options:
                print("Неверная опция!")
            action = content.choices[associations[option]].apply(self.state)
            print(action)
            break


game = Game(state)
game.run()
