#!/usr/bin/env python3
"""guard_proof.py — «стерегут ли фикстуры ИМЕННО ЭТУ правку»: откатить её и потребовать КРАСНОГО.

ЗАЧЕМ. Аппарат закрытия дефектов доказывает форму: пара фикстур существует, мутационные строки на
месте, хеши сходятся. Чего он не доказывает — что эта пара трогает ТОТ код, о котором расписка.
Три независимых ревью подряд находили в моих же починках одно и то же: якорь ссылался на чужую пару
(`check_source_map` закрыт стражем, гоняющим `check_layout`), must-NOT не касалась изменённого кода,
мутация ломала модуль вместо ослабления семантики. Каждый раз это обнаруживал ОДИН приём — откатить
правку на копии и посмотреть, покраснеет ли суита. Приём дешёвый, повторяемый и не зависящий от того,
что автор думает о своей фикстуре, — значит ему место в инструменте, а не в добрых намерениях.

ЧТО ЭТО НЕ ДОКАЗЫВАЕТ, чтобы не выдавать за большее. Красная суита говорит «какая-то фикстура заметила
откат», а не «правка верна» и не «фикстура хорошо написана». Это НИЖНЯЯ граница: без неё расписка
ничего не значит; с ней она значит ровно то, что заявляет.

ИСПОЛЬЗОВАНИЕ:
    guard_proof.py <скилл> <файл> [файл ...] [--ref <git-ref>]
        скилл — factcheck | research | bildredaktor (чью суиту гонять)
        файл  — путь от корня репозитория; откатывается к версии из `--ref` (по умолчанию HEAD~1)

Код возврата: 0 — откат ПОКРАСНЕЛ (фикстуры стерегут), 1 — остался зелёным (не стерегут),
2 — прогон невозможен (нет файла, нет ревизии, не собралась копия).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

SUITES = {
    "factcheck": ("bash", "selftest.sh"),
    "bildredaktor": ("bash", "selftest.sh"),
    "research": ("python3", "check_brief_selftest.py"),
}
TIMEOUT_SEC = 1800


def repo_root():
    """Корень репозитория от РЕАЛЬНОГО расположения файла: скрипты симлинкуются в соседние скиллы."""
    return os.path.realpath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "..")
    )


def file_at(ref, path, root):
    """Содержимое файла на ревизии. None — файла там не было (значит правка его СОЗДАЛА)."""
    run = subprocess.run(
        ["git", "-C", root, "show", f"{ref}:{path}"], capture_output=True, text=True
    )
    return run.stdout if run.returncode == 0 else None


def main():
    parser = argparse.ArgumentParser(description="стерегут ли фикстуры именно эту правку")
    parser.add_argument("skill", choices=sorted(SUITES))
    parser.add_argument("files", nargs="+", help="пути от корня репозитория")
    parser.add_argument(
        "--ref", default="HEAD~1", help="ревизия, к которой откатывать (по умолч. HEAD~1)"
    )
    parser.add_argument(
        "--root",
        help="корень репозитория (по умолчанию выводится от расположения самого файла); нужен, чтобы "
        "инструмент можно было проверить на СОБСТВЕННОЙ фикстуре, а не только на живом репозитории",
    )
    args = parser.parse_args()

    root = os.path.abspath(args.root) if args.root else repo_root()
    scripts = os.path.join(root, "skills", args.skill, "scripts")
    if not os.path.isdir(scripts):
        print(f"✗ guard_proof: нет папки скриптов скилла — {scripts}")
        return 2

    reverted = {}
    for rel in args.files:
        if not os.path.isfile(os.path.join(root, rel)):
            print(f"✗ guard_proof: файла нет в рабочем дереве — {rel}")
            return 2
        reverted[rel] = file_at(args.ref, rel, root)

    tmp = tempfile.mkdtemp(prefix="guard-proof-")
    try:
        copy = os.path.join(tmp, "scripts")
        shutil.copytree(scripts, copy, symlinks=False)
        # Кросс-скилловые соседи: копия дерева ПЛОСКАЯ, а суиты research/bildredaktor опираются на
        # общие модули фактчека. Копируем их рядом — тем же правилом, а не списком имён.
        # …но кладём их НЕ в опрашиваемый каталог, а рядом и на PYTHONPATH. Прежняя редакция сыпала
        # все `*.py` фактчека прямо в копию скриптов скилла — и вакуумный свип внутри суиты research
        # начинал опрашивать ЧУЖИЕ гейты, которых в раскладке research нет. Суита падала независимо
        # от отката, а приём докладывал «✅ стерегут» на ЛЮБУЮ правку, включая холостую: расписка по
        # research не значила ничего. Нашло независимое ревью холостым откатом (файл сам в себя).
        canon = os.path.join(root, "skills", "factcheck", "scripts")
        deps = os.path.join(tmp, "deps")
        os.makedirs(deps, exist_ok=True)
        if os.path.realpath(canon) != os.path.realpath(scripts):
            for name in os.listdir(canon):
                if name.endswith(".py") and not os.path.exists(os.path.join(copy, name)):
                    shutil.copy2(os.path.join(canon, name), os.path.join(deps, name))
        # Суиты читают не только скрипты: research берёт из `reference/` шаблон брифа и контракты
        # ролей. Без них прогон падает ТРЕЙСБЕКОМ — а трейсбек приём засчитывал за покраснение, то
        # есть докладывал «✅ стерегут» на любую правку, включая холостую. Кладём `reference/` рядом,
        # сохраняя раскладку: суита ищет его как `../reference` от каталога скриптов.
        for skill_name in {args.skill, "factcheck"}:
            ref_src = os.path.join(root, "skills", skill_name, "reference")
            if os.path.isdir(ref_src):
                shutil.copytree(
                    ref_src, os.path.join(tmp, "reference"), symlinks=False, dirs_exist_ok=True
                )
        routes = os.path.join(root, "skills", "factcheck", "reference", "runtime_routes.json")
        if os.path.isfile(routes):
            shutil.copy2(routes, os.path.join(copy, "runtime_routes.json"))
        # Реестр нужен фикстуре ссылок: копия дерева ПЛОСКАЯ, соседа по раскладке в ней нет, и без
        # этого приём докладывал бы ложное «стерегут» за счёт постороннего красного. Ложный красный в
        # доказывающем харнессе не безобиден: он подмешивается к настоящим падениям и делает
        # расписку менее читаемой, чем её отсутствие. Тот же приём, что в мутационной суите.
        ledger = os.path.join(root, "skills", "_ISSUES_TOOLKIT.md")
        if os.path.isfile(ledger):
            shutil.copy2(ledger, os.path.join(copy, "_ISSUES_TOOLKIT.md"))

        touched = []
        for rel, old in reverted.items():
            name = os.path.basename(rel)
            target = os.path.join(copy, name)
            if old is None:
                # Правка СОЗДАЛА файл: откат — это его отсутствие.
                if os.path.exists(target):
                    os.remove(target)
                    touched.append(f"{name} (удалён: на {args.ref} его не было)")
                continue
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(old)
            touched.append(name)
        if not touched:
            print("✗ guard_proof: ни один файл не откатился — доказывать нечего")
            return 2

        runner, suite = SUITES[args.skill]
        env = os.environ.copy()
        env["EDITOR_TOOLBOX_RUNTIME_ROUTES"] = os.path.join(copy, "runtime_routes.json")
        env["EVAL_CASES"] = os.path.join(root, "skills", "factcheck", "eval", "cases")
        env["PYTHONPATH"] = os.pathsep.join(
            [deps] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])
        )
        try:
            run = subprocess.run(
                [runner, os.path.join(copy, suite)],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SEC,
                env=env,
            )
        except subprocess.TimeoutExpired:
            print(f"✗ guard_proof: суита {args.skill} не завершилась за {TIMEOUT_SEC}с")
            return 2

        out = run.stdout + run.stderr
        red = [line for line in out.split("\n") if line.strip().startswith("❌")]
        print(f"откат к {args.ref}: {', '.join(touched)}")
        # СЛОМАЛОСЬ ≠ ПОКРАСНЕЛО. Ненулевой код от УПАВШЕЙ суиты доказывает не то, что фикстуры
        # стерегут правку, а лишь то, что прогон не состоялся. Пока это не различалось, приём
        # выдавал «✅ стерегут» на холостом откате — и расписка по целому скиллу ничего не значила.
        # Тот же класс, что «НЕ ПРОВЕРЕНО ≠ ПРОЙДЕНО» у мета-стража бильд-редактуры.
        if run.returncode != 0 and not red and "Traceback (most recent call last)" in out:
            print(
                "✗ guard_proof: прогон НЕПРИГОДЕН — суита упала трейсбеком, ни одна фикстура "
                "не высказалась. Это не доказательство: почини прогон и повтори.\n"
                + "\n".join(out.strip().split("\n")[-6:])
            )
            return 2
        if run.returncode == 0:
            print(
                f"✗ фикстуры НЕ стерегут эту правку: суита {args.skill} осталась ЗЕЛЁНОЙ на откате.\n"
                "  Расписка о починке в этом виде ничего не доказывает: пара может ссылаться на чужой\n"
                "  якорь, а must-NOT — не касаться изменённого кода. Допиши фикстуру, которая краснеет\n"
                "  ИМЕННО от этого отката."
            )
            return 1
        print(f"✅ стерегут: суита {args.skill} краснеет на откате ({len(red)} фикстур)")
        for line in red[:12]:
            print(f"     {line.strip()}")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
