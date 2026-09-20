from dataclasses import dataclass, field

from damsel.actions.choices import GenericChoices
from damsel.model.content import Choice, GameContent, UIContext
from damsel.model.state import GameState
from damsel.model.types import ItemId, LocationId, ObjectId
from damsel.rendering.renderer import GameRenderer


@dataclass
class Game:
    state: GameState
    content: GameContent
    renderer: GameRenderer
    _generic: GenericChoices = field(init=False)
    time: int = 0
    _previous_tick_location: LocationId | None = None
    ui_context: list[UIContext] = field(default_factory=lambda: [UIContext.LOCATION])
    focused_item: ItemId | None = None
    focused_object: ObjectId | None = None

    def __post_init__(self) -> None:
        self._generic = GenericChoices(self.state, self.content)

    def run(self) -> None:
        while self.time < 10:
            self._tick()

    def _tick(self) -> None:
        self.time += 1
        verbose = self.state.current_location not in self.state.visited_locations
        location_changed = self.state.current_location != self._previous_tick_location

        choices_dict = self._numbered(self.get_contextual_choices())

        if self.ui_context[-1] == UIContext.LOCATION and (verbose or location_changed):
            print(self.renderer.render_location(verbose))
            self.state.set_location_visited()

        print(self.renderer.render_choices(choices_dict))
        self._process(choices_dict)

    def get_contextual_choices(self) -> list[Choice]:
        ctx = self.ui_context[-1]
        if ctx == UIContext.LOCATION:
            return self._generic.get_location_actions()
        elif ctx ==UIContext.INVENTORY:
            return self._generic.get_inventory_actions()
        elif ctx ==UIContext.ITEM_FOCUS:
            return self._generic.get_item_focus_actions(self.focused_item)
        elif ctx ==UIContext.OBJECT_FOCUS:
            return self._generic.get_object_focus_actions(self.focused_object)
        return []

    def _numbered(self, choices: list[Choice]) -> dict[str, Choice]:
        return {str(n): c for n, c in enumerate(choices, 1)}

    def _process(self, choices_dict: dict[str, Choice]) -> None:
        self._previous_tick_location = self.state.current_location
        while True:
            option = input("> ")
            if option not in choices_dict:
                print("Неверная опция!")
                continue
            choice = choices_dict[option]

            # Обработка UI-навигации
            if choice.is_ui:
                self._handle_ui_navigation(choice)
                break

            # Обработка игровых действий
            action_description = choice.apply(self.state, self.content)
            print(action_description)
            break

    def _handle_ui_navigation(self, choice: Choice):
        nav_type = choice.id
        if nav_type == "ui_back":
            if len(self.ui_context) > 1:
                self.ui_context.pop()
                self.focused_item = None
                self.focused_object = None
        elif nav_type == "ui_inventory":
            self.ui_context.append(UIContext.INVENTORY)
        elif nav_type.startswith("ui_focus_obj"):
            self.focused_object = ObjectId(nav_type.split("^")[-1])
            self.ui_context.append(UIContext.OBJECT_FOCUS)
        elif nav_type.startswith("ui_focus_item"):
            self.focused_item = ItemId(nav_type.split("^")[-1])
            self.ui_context.append(UIContext.ITEM_FOCUS)
