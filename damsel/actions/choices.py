from damsel.actions.effects import EFFECTS
from damsel.model.content import Choice, GameContent, Result
from damsel.model.state import GameState
from damsel.model.types import INVENTORY_LOCATION_ID, ItemId, ObjectId


class GenericChoices:
    def __init__(self, state: GameState, content: GameContent) -> None:
        self.state = state
        self.content = content

    def _make_ui_choice(self, text: str, ui_id: str) -> Choice:
        return Choice(id=ui_id, text=text, is_ui=True)

    def get_location_actions(self) -> list[Choice]:
        choices: list[Choice] = []
        # Статические выборы локации
        for c in self.content.choices.values():
            if c.is_available(self.state, self.content):
                choices.append(c)
        # Динамические действия с предметами на полу
        choices.extend(self.pickup())
        choices.extend(self.open())
        choices.extend(self.close())

        # Навигация
        choices.append(self._make_ui_choice("Заглянуть в инвентарь", "ui_inventory"))
        # опция ничего не делает, так как ни на чем не сфокусирована
        # нужно так же проходиться циклом по предметам, лежащим на полу
        choices.append(
            self._make_ui_choice("Взаимодействовать с предметом", "ui_interact_placeholder")
        )
        # Генерируем фокус-опции для объектов
        for fid in self.content.locations[self.state.current_location].objects:
            furn = self.content.furniture[fid]
            choices.append(
                self._make_ui_choice(
                    f"Взаимодействовать с {furn.name}", f"ui_focus_obj^{fid}"
                )
            )
        return choices

    def get_inventory_actions(self) -> list[Choice]:
        choices: list[Choice] = []
        for iid in self.state.locations_items[INVENTORY_LOCATION_ID]:
            item = self.content.items[iid]
            choices.append(
                self._make_ui_choice(f"Осмотреть {item.name}", f"ui_focus_item^{iid}")
            )
        choices.append(self._make_ui_choice("Выйти из инвентаря.", "ui_back"))
        return choices

    def get_item_focus_actions(self, item_id: ItemId) -> list[Choice]:
        choices: list[Choice] = []
        item = self.content.items[item_id]
        # Осмотр
        choices.append(
            Choice(
                id=f"examine_{item_id}",
                text=f"Осмотреть {item.name}",
                # нужно переделать на result = Result("genetic_exam", {"item": iid})
                result_text=self.content.items[item_id].description,
                do=[],
            )
        )
        # Выбросить
        choices.extend(self.drop_for_item(item_id))
        # статические выборы для предметов в инвентаре
        for c in self.content.choices.values():
            if c.is_available(self.state, self.content) and any(
                "has item" in str(e) for e in c.do
            ):
                choices.append(c)
        choices.append(self._make_ui_choice("Назад.", "ui_back"))
        return choices

    def get_object_focus_actions(self, obj_id: ObjectId) -> list[Choice]:
        choices: list[Choice] = []
        furn = self.content.furniture[obj_id]
        choices.append(
            Choice(id=f"examine_{obj_id}", text=f"Осмотреть: {furn.name}", result_text=furn.description, do=[])
        )
        # Открыть/Закрыть
        choices.extend(self.open_for_object(obj_id))
        choices.extend(self.close_for_object(obj_id))

        # вынуть предметы из контейнера
        if furn.is_container and self.state.objects[obj_id].flags.get("open"):
            for item_id in self.state.objects[obj_id].items:
                choices.append(
                    Choice(
                        id=f"take_from_{obj_id}_{item_id}",
                        text=f"Взять {self.content.items[item_id].name}",
                        do=[EFFECTS["get_item"]({"item": item_id})],
                        result=Result("generic_pickup", {"item": item_id}),
                    )
                )

        choices.append(self._make_ui_choice("Назад.", "ui_back"))
        return choices

    def drop_for_item(self, item_id: ItemId) -> list[Choice]:
        item = self.content.items[item_id]
        return [
            Choice(
                id=f"drop_{item_id}",
                text=f"Выбросить {item.name}",
                result=Result("generic_drop", {"item": item_id}),
                do=[EFFECTS["drop_item"]({"item": item_id})],
            )
        ]

    def open_for_object(self, fid: ObjectId) -> list[Choice]:
        furn = self.content.furniture[fid]
        if not furn.can_open:
            return []
        obj = self.state.objects[fid]
        if obj.flags["open"] or obj.flags["locked"]:
            return []
        return [
            Choice(
                id=f"open_{fid}",
                text=f"Открыть {furn.name}",
                result=Result("generic_open", {"object": fid}),
                do=[EFFECTS["open_object"]({"object": fid})],
            )
        ]

    def close_for_object(self, fid: ObjectId) -> list[Choice]:
        furn = self.content.furniture[fid]
        if not furn.can_open:
            return []
        obj = self.state.objects[fid]
        if not obj.flags["open"] or obj.flags["locked"]:
            return []
        return [
            Choice(
                id=f"close_{fid}",
                text=f"Закрыть {furn.name}",
                result=Result("generic_close", {"object": fid}),
                do=[EFFECTS["close_object"]({"object": fid})],
            )
        ]

    def pickup(self) -> list[Choice]:
        options = []
        for iid in self.state.locations_items[self.state.current_location]:
            item = self.content.items[iid]
            options.append(
                Choice(
                    id=f"pick_up_{iid}",
                    text=f"Взять {item.name}",
                    result=Result("generic_pickup", {"item": iid}),
                    do=[EFFECTS["get_item"]({"item": iid})],
                )
            )
        return sorted(options, key=lambda c: c.text)

    def drop(self) -> list[Choice]:
        options = []
        for iid in self.state.locations_items[INVENTORY_LOCATION_ID]:
            item = self.content.items[iid]
            options.append(
                Choice(
                    id=f"drop_{iid}",
                    text=f"Выбросить {item.name}",
                    result=Result("generic_drop", {"item": iid}),
                    do=[EFFECTS["drop_item"]({"item": iid})],
                )
            )
        return sorted(options, key=lambda c: c.text)

    def open(self) -> list[Choice]:
        options = []
        for fid in self.content.locations[self.state.current_location].objects:
            furn = self.content.furniture[fid]
            obj = self.state.objects[fid]
            if furn.can_open and not obj.flags["open"] and not obj.flags["locked"]:
                options.append(
                    Choice(
                        id=f"open_{fid}",
                        text=f"Открыть {furn.name}",
                        result=Result("generic_open", {"object": fid}),
                        do=[EFFECTS["open_object"]({"object": fid})],
                    )
                )
        return options

    def close(self) -> list[Choice]:
        options = []
        for fid in self.content.locations[self.state.current_location].objects:
            furn = self.content.furniture[fid]
            obj = self.state.objects[fid]
            if furn.can_open and obj.flags["open"] and not obj.flags["locked"]:
                options.append(
                    Choice(
                        id=f"close_{fid}",
                        text=f"Закрыть {furn.name}",
                        result=Result("generic_close", {"object": fid}),
                        do=[EFFECTS["close_object"]({"object": fid})],
                    )
                )
        return options
