# Vacuous-pass sweep

Two tools that ask a question about automated checks that the checks cannot ask about themselves:
**can this check report a pass without having done the work it claims to do?**

They were extracted from a claim-verification harness I build and operate for fact-checking
popular-science video scripts. The harness has 51 release checks; a green run blocks or releases
real editorial work. The tools here are the layer above those checks.

The code is unmodified from the working system, so its console output is Russian — the harness
serves Russian deliverables. Every line it prints is glossed in English below.

---

## Try it in ten seconds

`demo/` holds two deliberately tiny checks. One is honest. One has the defect.

```bash
python3 vacuous_sweep.py demo
```

```
  ✅ check_honest: не утверждает положительного о непроделанной работе
  ❌ check_vacuous: вышел НУЛЁМ на несуществующем пути (класс TK-0002/TK-0066)
       напечатал: nothing to check
       чинить так: несуществующий путь — отказ с ненулевым кодом. Ноль объектов в
       НАСТОЯЩЕМ выпуске остаётся законным зелёным: свип зондирует не его.
✗ вакуумных гейтов: 1 — ноль проверок неотличим от нуля нарушений
```

In English:

> ✅ `check_honest`: makes no positive claim about work it did not do.
> ❌ `check_vacuous`: **exited zero on a nonexistent path.** It printed `nothing to check`.
> Fix: a nonexistent path must be a refusal with a non-zero exit code. Zero objects in a *real*
> episode remains a legitimate pass — the sweep does not probe that case.
> ✗ 1 vacuous check: zero inspections is indistinguishable from zero violations.

Exit code is `1`. The two demo checks differ by about six lines; the difference is the entire point.

---

## What the probe requires

A check is put on trial and must satisfy two conditions.

1. **Refuse a nonexistent path**, at *every* argument count it accepts. Walking all arities is not
   thoroughness for its own sake: a real check took a cache directory as its second positional
   argument, and that branch bypassed its only path check — so it was honest at one arity and
   vacuous at another.
2. **Name a number** when run against an existing but empty input. Zero objects in a real episode
   is a legitimate outcome; an *invisible* zero is indistinguishable from a universal claim about
   work that was never done. A count cannot be satisfied by wording and does not depend on the
   language the check prints in.

An argument-parsing abort does not count as an answer. Under that cover three checks in the
original system were not merely green but walking the disk for 25 seconds.

The bar is deliberately low. It is a floor, not a ceiling.

## Why a sweep and not a list of offenders

Nine checks had already been fixed by name. The class came back in new code: three checks written
afterwards printed conclusions about corpora they had never opened. A defect closed by a one-time
action returns, so the carrier of the fix has to sit one class above the defect.

The first version of the probe found nothing, because its fake path sat inside a real temporary
directory. Moving the probe to a nonexistent path at the filesystem root immediately exposed a
check that resolved the miss to `/` and began scanning the entire disk. A degenerate-input test is
only as good as how degenerate the input is.

## What it does not prove

- It never judges whether a verdict is **correct**. It only establishes that the check reached its
  input before claiming the input was clean.
- A check can still hide a zero behind an unrelated number. That limit is recorded rather than
  papered over.
- Detecting whether a non-`check_*` script makes a pass/fail claim is a judgment call, so those are
  enrolled by hand via `--also` — a name list, the very pattern this tool exists to replace.

---

## `guard_proof.py`

A second, smaller tool answering a different question: **do the tests guard *this particular* fix?**

Three independent reviews in a row found the same thing in my own repairs — a regression fixture
anchored to a different check, or a negative case that never touched the changed code. Each time it
was caught by one move: revert the fix on a copy and see whether the suite goes red. That move
belongs in a tool rather than in good intentions.

```bash
python3 guard_proof.py <skill> <file> [file ...] [--ref <git-ref>]
```

Exit `0` means the suite went red when the change was reverted — the fixtures do guard it. Exit `1`
means it stayed green, so the receipt proves nothing.

It does not prove the fix is correct, nor that the fixture is well written. It is a lower bound,
without which the receipt is empty.

---

## Self-test

Both the predicate and the tool are tested two-sided — a rule must fire where it should and stay
silent where it should not.

```bash
python3 vacuous_sweep.py --selftest
```

Eleven cases, exit `0`. In English, they check that: a non-zero exit is never vacuous; a
reassuring *phrase* no longer excuses a check; a universal claim is vacuous; a silent zero-exit is
vacuous; an argument-parsing abort is not an answer, while a genuine refusal is; a refusal need not
state its scope, but a pass must; a stated property is not a stated count; and silence is not a
scope.

## Files

| File | Lines | Purpose |
|---|---|---|
| `vacuous_sweep.py` | 431 | Probes every check with degenerate input |
| `guard_proof.py` | 190 | Reverts a fix and requires the suite to go red |
| `demo/check_honest.py` | 20 | Refuses a bad path, states a count |
| `demo/check_vacuous.py` | 17 | The defect, minimally |

Python 3.9+, standard library only. No dependencies, no configuration.

## Provenance

This is a **snapshot for reading**, not a fork. The canonical copies live in the harness they came
from and are symlinked into three skills; edits belong there. Keeping a second editable copy is the
same divergence class these tools exist to catch.

<!-- Daria: paste your own write-up of the finding here, or link it. This README is documentation;
     that piece is the argument, and it should be in your words. -->
