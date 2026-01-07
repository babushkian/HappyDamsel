from definitions import Choice
from loader import LOCATIONS, CHOICES
from definitions import ItemId, ObjectId, LocationId, GameState, Inventory


# идентификаторы
RUSTY_KEY = ItemId("rusty_key")
# GOLD_RING = ItemId("gold_ring")
BOX = ObjectId("wooden_box")
# CHEST = ObjectId("iron_chest")
ATTIC = LocationId("attic")
# HALL = LocationId("hall")


# инвентарь с ключом
inventory = Inventory(items={RUSTY_KEY: 1})

# состояние игры
state = GameState(
    current_location=ATTIC,
    # locations={ATTIC: attic_loc, HALL: hall_loc},
    locations=LOCATIONS,
    inventory=inventory,
    flags={},
)


open_box = CHOICES["open_box"]
go_down = CHOICES["go_down_to_hall"]
up_to_attic = CHOICES["go_up_to_attic"]


def show_inventory(inv: Inventory):
    return {k.value: v for k, v in inv.items.items()}


print("Текущая локация:", state.location().name)  # Чердак
print("Инвентарь до:", show_inventory(state.inventory))

# Попробуем открыть шкатулку в чердаке
if open_box.is_available():
    open_box.apply()
    print("Шкатулка открыта, содержимое добавлено в инвентарь.")
else:
    print("Условия для открытия шкатулки не выполнены.")

print("Инвентарь после:", show_inventory(state.inventory))

# Перейдём вниз (через эффект)
if go_down.is_available():
    go_down.apply()
    print("После перемещения — локация:", state.location().name)

# Попытка получить контейнер, который не в текущей локации — выдаст ошибку
try:
    state.get_container(BOX)  # BOX осталась в локации Чердак
except ValueError as exc:
    print("Ошибка доступа к контейнеру:", exc)

if up_to_attic.is_available():
    up_to_attic.apply()
    print("После перемещения наверх — локация:", state.location().name)