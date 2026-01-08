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
print("=====================")
pprint(content)
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


    def render_choices(self):
        print(content.choices)
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
            content.choices[associations[option]].apply(self.state)
            break


game = Game(state)
game.run()

# open_box = content.choices["open_box"]
# go_down = content.choices["go_down_to_hall"]
# up_to_attic = content.choices["go_up_to_attic"]
#
#
# def show_inventory(inv: Inventory):
#     return {k.value: v for k, v in inv.items.items()}
#
#
# print("Текущая локация:", state.location().name)  # Чердак
# print("Инвентарь до:", show_inventory(state.inventory))
#
# # Попробуем открыть шкатулку в чердаке
# if open_box.is_available(state):
#     open_box.apply(state)
#     print("Шкатулка открыта, содержимое добавлено в инвентарь.")
# else:
#     print("Условия для открытия шкатулки не выполнены.")
#
# print("Инвентарь после:", show_inventory(state.inventory))
#
# # Перейдём вниз (через эффект)
# if go_down.is_available(state):
#     go_down.apply(state)
#     print("После перемещения — локация:", state.location().name)
#
# # Попытка получить контейнер, который не в текущей локации — выдаст ошибку
# try:
#     state.get_container(BOX)  # BOX осталась в локации Чердак
# except ValueError as exc:
#     print("Ошибка доступа к контейнеру:", exc)
#
# if up_to_attic.is_available(state):
#     up_to_attic.apply(state)
#     print("После перемещения наверх — локация:", state.location().name)