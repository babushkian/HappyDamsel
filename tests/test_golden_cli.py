"""Golden-тесты CLI: игра прогоняется subprocess'ом со скриптом ввода,
вывод сравнивается с эталонным. Защищает поведение при рефакторинге.

Каждый сценарий — ровно 10 действий: движок сам завершает игру после 10 тиков,
поэтому процесс корректно выходит без EOFError.

Регенерация эталонов: REGEN_GOLDEN=1 uv run pytest tests/test_golden_cli.py
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"

# Сценарии — последовательности номеров опций на каждый тик.
SCENARIOS: dict[str, list[str]] = {
    # Подобрать молоток/гвоздь → инвентарь → фокус на ключе → осмотр → назад →
    # выйти → открыть шкатулку → спуститься → подобрать розовый ключ
    "attic_inventory": ["4", "3", "3", "1", "1", "3", "4", "1", "1", "2"],
    # Фокус на розовой шкатулке → осмотр → назад → вниз → открыть сундук →
    # фокус на сундуке → взять записку → закрыть → назад → фокус на двери
    "hall_chest": ["7", "1", "2", "2", "3", "7", "3", "2", "3", "9"],
    # Вниз → включить выключатель → открыть дверь → войти в кладовку (свет!) →
    # фокус на стеллаже → взять стамеску → осмотреть стеллаж → назад → выйти
    "closet_light": ["2", "5", "4", "2", "4", "2", "1", "2", "1", "2"],
}


def run_game(inputs: list[str]) -> str:
    proc = subprocess.run(
        [sys.executable, "-u", "-m", "damsel"],
        input="\n".join(inputs) + "\n",
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=30,
    )
    assert proc.returncode == 0, f"игра завершилась с кодом {proc.returncode}: {proc.stderr}"
    return proc.stdout


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_golden(name: str) -> None:
    """Прогон CLI subprocess'ом по сценарию (номера опций на каждый тик) и
    побайтовое сравнение вывода с эталоном. Ловит любые изменения видимого
    поведения: тексты, порядок и состав опций, форматирование рендера."""
    golden_path = GOLDEN_DIR / f"{name}.txt"
    actual = run_game(SCENARIOS[name])
    if os.environ.get("REGEN_GOLDEN"):
        golden_path.write_text(actual, encoding="utf-8")
        pytest.skip(f"эталон {golden_path.name} перезаписан")
    expected = golden_path.read_text(encoding="utf-8")
    assert actual == expected, f"вывод сценария {name!r} отличается от эталона"
