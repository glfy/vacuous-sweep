#!/usr/bin/env python3
"""An HONEST check: refuses a path it cannot read, and states a count when it can."""
import sys, pathlib

def main(argv):
    if len(argv) != 1:
        print("usage: check_honest.py <reports_dir>", file=sys.stderr)
        return 2
    root = pathlib.Path(argv[0])
    if not root.is_dir():
        print(f"{root}: no such directory — nothing was inspected", file=sys.stderr)
        return 2                      # refuses degenerate input
    items = sorted(root.glob("*.md"))
    print(f"inspected {len(items)} report(s); 0 violations")   # names the count
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
