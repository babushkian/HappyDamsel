from dataclasses import dataclass, field
from damsel.model.content import Choice, GameContent
from damsel.model.state import GameState
from damsel.model.types import LocationId
from damsel.rendering.renderer import GameRenderer
from damsel.actions.choices import GenericChoices


@dataclass
class Game:
    state: GameState
    content: GameContent
    renderer: GameRenderer
    _generic: GenericChoices = field(init=False)
    _previous_location: LocationId | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self._generic = GenericChoices(self.state, self.content)

    def run(self) -> None:
        while True:
            self._tick()

    def _tick(self) -> None:
        verbose = self.state.current_location not in self.state.visited_locations
        location_changed = self.state.current_location != self._previous_location

        choices_dict = self._numbered(self._available_choices())

        if verbose or location_changed:
            print(self.renderer.render_location(verbose))
            self.state.set_location_visited()

        print(self.renderer.render_choices(choices_dict))
        self._process(choices_dict)

    def _available_choices(self) -> list[Choice]:
        choices = [c for c in self.content.choices.values() if c.is_available(self.state, self.content)]
        choices.extend(self._generic.pickup())
        choices.extend(self._generic.open())
        choices.extend(self._generic.close())
        choices.extend(self._generic.drop())
        return choices

    def _numbered(self, choices: list[Choice]) -> dict[str, Choice]:
        return {str(n): c for n, c in enumerate(choices, 1)}

    def _process(self, choices_dict: dict[str, Choice]) -> None:
        self._previous_location = self.state.current_location
        while True:
            option = input("> ")
            if option not in choices_dict:
                print("Неверная опция!")
                continue
            result = choices_dict[option].apply(self.state, self.content)
            if result:
                print(result)
            break
