from damsel.world.builder import ContentBuilder
from damsel.world.loader import YamlLoader
from damsel.rendering.renderer import GameRenderer
from damsel.engine import Game


def main() -> None:
    content, state = ContentBuilder(YamlLoader).build()
    renderer = GameRenderer(state, content)
    Game(state, content, renderer).run()


if __name__ == "__main__":
    main()
