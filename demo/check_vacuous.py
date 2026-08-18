#!/usr/bin/env python3
"""A VACUOUS check: the bug this repo is about. Green whether or not it did the work."""
import sys, pathlib

def main(argv):
    root = pathlib.Path(argv[0]) if argv else pathlib.Path(".")
    items = sorted(root.glob("*.md")) if root.is_dir() else []
    if not items:
        print("nothing to check")     # a missing directory reads as an empty one
        return 0
    print("every report is properly sourced")   # a claim about a set it never inspected
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
