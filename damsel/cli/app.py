"""CLI-фронтенд: тонкая обёртка над GameSession.

Владеет игровым циклом, вводом-выводом и обработкой Ctrl+C/Ctrl+D.
Лимит в 10 действий — решение CLI (демо-режим); другие фронтенды
передают max_ticks=None и работают без лимита.
"""

from __future__ import annotations

from damsel.cli.renderer import render_view
from damsel.model.view import ActionView, GameView
from damsel.session import GameSession
from damsel.world.builder import ContentBuilder
from damsel.world.loader import YamlLoader

MAX_TICKS = 10


def main() -> None:
    content, state = ContentBuilder(YamlLoader).build()
    session = GameSession(content, state, max_ticks=MAX_TICKS)
    try:
        _run(session)
    except (KeyboardInterrupt, EOFError):
        print("\nДо встречи!")


def _run(session: GameSession) -> None:
    view = session.get_view()
    while not view.finished:
        print(render_view(view), end="")
        action = _read_action(view)
        session.dispatch(action.id)
        view = session.get_view()
    # результат последнего действия попадает уже в завершённый вид — показываем его
    if view.message:
        print(view.message)
    print("Игра завершена. До встречи!")


def _read_action(view: GameView) -> ActionView:
    while True:
        raw = input("> ")
        action = _parse_option(view, raw)
        if action is not None:
            return action
        print("Неверная опция!")


def _parse_option(view: GameView, raw: str) -> ActionView | None:
    if not raw.isdigit():
        return None
    index = int(raw) - 1
    if not 0 <= index < len(view.actions):
        return None
    return view.actions[index]
