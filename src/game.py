from init_content import ContentLoader
from loaders import YamlLoader
from renderer import GameRenderer
from engine import Game


def main() -> None:
    content, state = ContentLoader(YamlLoader).init_content()
    renderer = GameRenderer(state, content)
    Game(state, content, renderer).run()


if __name__ == "__main__":
    main()
