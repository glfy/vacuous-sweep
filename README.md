# Vacuous-pass sweep

An automated check can report success without ever having looked at anything. It happens when the
check treats missing input as empty input: no files found, nothing wrong, exit zero, green.

This tool finds checks that do that. It does one thing — it runs each check on input there is
nothing to say about, and looks at what the check says anyway.

The tools come from a claim-verification harness I build and operate for fact-checking
popular-science video scripts. It has 51 checks, and a green run releases real editorial work.
The code here is unmodified, so it prints in Russian; every line is translated below.

## How it works

There are two probes, and they ask two different questions.

**Probe 1 — a path that does not exist.** The question is: did you reach your input at all?

```
$ python3 demo/check_honest.py  /nonexistent-abc/def
/nonexistent-abc/def: no such directory — nothing was inspected
exit 2

$ python3 demo/check_vacuous.py /nonexistent-abc/def
nothing to check
exit 0
```

Zero means "all good". The second check reported all-good about a directory that isn't there.
That is the whole detection, and the rule behind it is one line: a nonexistent path must produce a
non-zero exit.

**Probe 2 — a directory that exists but is empty.** The question is: when you say everything is
fine, over how many things?

```
$ python3 demo/check_honest.py  <empty dir>
inspected 0 report(s); 0 violations
exit 0

$ python3 demo/check_vacuous.py <empty dir>
nothing to check
exit 0
```

Both exit zero, and both are entitled to. Zero objects in a real folder is a legitimate pass.
The difference is that one of them **says a number**. An invisible zero cannot be told apart from
a claim about everything.

## Try it

```bash
python3 vacuous_sweep.py demo
```

```
  ✅ check_honest: не утверждает положительного о непроделанной работе
  ❌ check_vacuous: вышел НУЛЁМ на несуществующем пути (класс TK-0002/TK-0066)
       напечатал: nothing to check
       чинить так: несуществующий путь — отказ с ненулевым кодом.
✗ вакуумных гейтов: 1 — ноль проверок неотличим от нуля нарушений
```

> ✅ `check_honest` makes no positive claim about work it did not do.
> ❌ `check_vacuous` exited zero on a nonexistent path. It printed `nothing to check`.
> Fix: a nonexistent path must be a refusal with a non-zero exit code.
> ✗ 1 vacuous check — zero inspections is indistinguishable from zero violations.

Exit code `1`. The two demo checks differ by about six lines.

## Four details that turned out to matter

**A number, not a phrase.** Probe 2 asks for a digit rather than a reassuring sentence. A phrase can
be satisfied by wording and depends on the language the check prints in. A count cannot.

**Subtract the probe's own path first.** Temporary directory names contain digits, so a check could
satisfy probe 2 by echoing its own argument. Before this was fixed, the same run came back green 37
times out of 40 — a meta-check that flickered.

**Try every argument count, not the first one that answers.** Checks take different numbers of
arguments, so the probe passes the path once, twice, three times. If a check rejects the arguments,
that is not an answer: it never got as far as doing work. And it must refuse at *every* arity it
accepts — one real check was honest with one argument and vacuous with two, because the second
positional went down a branch that skipped the only path check.

**A timeout is its own finding.** No answer within 60 seconds on a nonexistent path means the check
is off scanning the disk. That is how a check that resolved a miss to `/` was found.

## Why a sweep instead of fixing the checks

Nine checks had already been fixed one at a time, by name. The class came back in new code: three
checks written afterwards printed conclusions about corpora they had never opened. A defect closed
by a one-time action returns. The fix has to sit one class above the defect.

The first version of the probe found nothing, because its fake path sat inside a real temporary
directory. Moving it to a nonexistent path at the filesystem root exposed the disk-walking check
immediately. A degenerate-input test is only as good as how degenerate the input is.

## What it does not prove

It never judges whether a verdict is **correct**. It establishes only that a check reached its input
before calling that input clean. It is a floor, not a ceiling.

A check can still hide a zero behind an unrelated number — that limit is recorded rather than
papered over. And whether a script makes a pass/fail claim at all is a judgment call, so scripts not
named `check_*` are enrolled by hand with `--also`: a name list, which is the very pattern this tool
exists to replace.

## The self-test

```bash
python3 vacuous_sweep.py --selftest
```

The predicate is a pure function and is tested from both sides — it must fire where it should and
stay silent where it should not. Eleven cases, exit `0`. Without this the sweep would be an
uninsured guard, capable of the exact failure it looks for.

## `guard_proof.py`

A second, smaller tool for a different question: **do the tests guard *this particular* fix?**

Three reviews in a row found the same thing in my own repairs — a regression fixture anchored to a
different check, or a negative case that never touched the changed code. Each time it was caught by
one move: revert the fix on a copy, and see whether the suite goes red.

```bash
python3 guard_proof.py <skill> <file> [file ...] [--ref <git-ref>]
```

Exit `0` — the suite went red, so the fixtures do guard the change. Exit `1` — it stayed green, so
the receipt proves nothing. It does not prove the fix is correct, or that the fixture is well
written. It is a lower bound, without which the receipt is empty.

## Files

| File | Lines | Purpose |
|---|---|---|
| `vacuous_sweep.py` | 431 | Probes every check with degenerate input |
| `guard_proof.py` | 190 | Reverts a change and requires the suite to go red |
| `demo/check_honest.py` | 20 | Refuses a bad path, states a count |
| `demo/check_vacuous.py` | 17 | The defect, minimally |

Python 3.9+, standard library only. No dependencies, no configuration.

## Provenance

A snapshot for reading, not a fork. The canonical copies live in the harness they came from and are
symlinked into three skills; edits belong there. A second editable copy would be the same
divergence this tool exists to catch.

<!-- Daria: paste your own write-up of the finding here, or link it. This README documents the
     tool; that piece is the argument, and it should be in your words. Delete this comment. -->
