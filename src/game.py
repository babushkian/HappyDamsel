from loader import LOCATIONS, CHOICES, INVENTORY
from definitions import ItemId, ObjectId, LocationId, GameState, Inventory


# идентификаторы
RUSTY_KEY = ItemId("rusty_key")
# GOLD_RING = ItemId("gold_ring")
BOX = ObjectId("wooden_box")
# CHEST = ObjectId("iron_chest")
ATTIC = LocationId("attic")
# HALL = LocationId("hall")



# состояние игры
state = GameState(
    current_location=ATTIC,
    locations=LOCATIONS,
    inventory=INVENTORY,
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
if open_box.is_available(state):
    open_box.apply(state)
    print("Шкатулка открыта, содержимое добавлено в инвентарь.")
else:
    print("Условия для открытия шкатулки не выполнены.")

print("Инвентарь после:", show_inventory(state.inventory))

# Перейдём вниз (через эффект)
if go_down.is_available(state):
    go_down.apply(state)
    print("После перемещения — локация:", state.location().name)

# Попытка получить контейнер, который не в текущей локации — выдаст ошибку
try:
    state.get_container(BOX)  # BOX осталась в локации Чердак
except ValueError as exc:
    print("Ошибка доступа к контейнеру:", exc)

if up_to_attic.is_available(state):
    up_to_attic.apply(state)
    print("После перемещения наверх — локация:", state.location().name)