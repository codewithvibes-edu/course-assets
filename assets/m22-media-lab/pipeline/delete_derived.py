"""Lesson 7, second half: prove the derived data can be found and removed.

The joined transcript lists every artifact derived from the source recording. This
tool walks that list plus the work directory, shows what exists, and with --apply
removes all of it and verifies nothing is left. The fixture and its records in
fixture/ stay; they are the source, not derivatives. The point of the drill: a
deletion promise is only real if the record names what to delete and the removal
can be checked afterward.

Usage, from assets/m22-media-lab/:
    python pipeline/delete_derived.py            (list what would go)
    python pipeline/delete_derived.py --apply    (remove it and verify)
"""

from __future__ import annotations

import argparse
import shutil

from common import KIT_ROOT, WORK_DIR


def collect() -> list:
    if not WORK_DIR.exists():
        return []
    return sorted(p for p in WORK_DIR.rglob("*") if p.is_file())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    found = collect()
    if not found:
        print("nothing derived exists; the drill starts after the pipeline has run")
        return

    total = sum(p.stat().st_size for p in found)
    joined = WORK_DIR / "transcript.json"
    print(f"derived artifacts under work/: {len(found)} files, {total / 1e6:.1f} MB")
    if joined.exists():
        import json
        listed = json.loads(joined.read_text())["derived_artifacts"]
        on_disk = {str(p.relative_to(WORK_DIR)) for p in found}
        unlisted = sorted(on_disk - set(listed) - {"transcript.json"})
        if unlisted:
            print("on disk but not named by the record (a deletion promise would miss these):")
            for name in unlisted:
                print(f"  {name}")
    for p in found[:20]:
        print(f"  {p.relative_to(KIT_ROOT)}")
    if len(found) > 20:
        print(f"  ... and {len(found) - 20} more")

    if not args.apply:
        print("\ndry run; rerun with --apply to remove everything above")
        return

    shutil.rmtree(WORK_DIR)
    leftovers = collect()
    if leftovers:
        raise SystemExit(f"DELETION INCOMPLETE: {len(leftovers)} files remain")
    print(f"\nremoved {len(found)} files; verified nothing remains under work/")
    print("the source fixture in fixture/ is untouched, as intended")


if __name__ == "__main__":
    main()
