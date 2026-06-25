#!/usr/bin/env python3
"""
Reconcile legacy (non-SPASE) instrument/observatory references to their
canonical SPASE-backed rows — the deterministic `apply=yes` subset of the HSSI
instrument/observatory backfill.

Context: HSSI's instrument/observatory vocabulary is now SPASE-backed, but a set
of legacy (non-SPASE) `InstrumentObservatory` rows are still referenced by
software. The backfill mapping (`backfill_mapping.csv`) classifies each legacy
row; only `apply=yes` rows are deterministic (resolved via the
helio.data.nasa.gov -> heliophysics.net -> SPASE bridge) and safe to apply
without human judgment. Everything else (`apply=no`) is left untouched for
manual review.

What this does (idempotent, dynamic — recompute everything from the CSVs, never
trust hard-coded counts):

  * For each `apply=yes` mapping row, repoint the legacy UUID to its canonical
    SPASE row UUID inside software.csv's inline comma-joined UUID columns
    `related_instruments` / `related_observatories`:
      - relation_action == "rewrite": same type -> replace UUID in place.
      - relation_action == "move":   type changes (e.g. SuperDARN
        Instrument -> Observatory) -> drop from related_instruments and add to
        related_observatories.
    De-duplicates within each cell.
  * After repointing, delete from instrument_observatory.csv every *legacy*
    (non-SPASE) row that is no longer referenced by any software: the now
    orphaned apply=yes rows plus any pre-existing unreferenced legacy orphans.
    `apply=no` rows stay referenced and are left intact.

Safety asserts: every canonical target exists and is a SPASE row; no `apply=no`
legacy row is ever deleted; every canonical target still exists after deletion;
no related_* cell ends up with duplicate UUIDs. CSV is written LF /
QUOTE_MINIMAL to match the committed seed format, so the git diff is minimal.

This is a Phase-2 change in the `production-csv-update` workflow. Re-run it
against a fresh prod snapshot before merge/import.

Usage:  python3 scripts/backfill/reconcile_instr_obs.py
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DB = os.path.join(REPO, "django", "website", "config", "db")
INSTR_OBS = os.path.join(DB, "instrument_observatory.csv")
SOFTWARE = os.path.join(DB, "software.csv")
MAPPING = os.path.join(HERE, "backfill_mapping.csv")

SPASE_PREFIX = "https://spase-metadata.org/"


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    return header, rows


def write_csv(path, header, rows):
    # LF + QUOTE_MINIMAL matches the committed seed format (tablib export,
    # CRLF-normalized to LF by the Phase-1 sync), keeping the diff minimal.
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        writer.writerows(rows)


def uuids(cell):
    return [x.strip() for x in (cell or "").split(",") if x.strip()]


def dedup(seq):
    return list(dict.fromkeys(seq))  # order-preserving


def main():
    # ---- mapping ----
    with open(MAPPING, newline="", encoding="utf-8") as f:
        mapping = list(csv.DictReader(f))
    apply_yes = [m for m in mapping if m["apply"].strip() == "yes"]
    apply_no_legacy = {
        m["legacy_uuid"].strip() for m in mapping if m["apply"].strip() != "yes"
    }

    # ---- instrument_observatory.csv ----
    io_header, io_rows = read_csv(INSTR_OBS)
    c = {name: i for i, name in enumerate(io_header)}
    id_to_row, ident_to_id, spase_ids = {}, {}, set()
    for row in io_rows:
        rid, ident = row[c["id"]], row[c["identifier"]]
        id_to_row[rid] = row
        if ident:
            ident_to_id[ident] = rid
        if ident.startswith(SPASE_PREFIX):
            spase_ids.add(rid)
    legacy_ids = set(id_to_row) - spase_ids

    # ---- build repoint table (legacy_id -> (canonical_id, action)) ----
    repoint = {}
    for m in apply_yes:
        legacy = m["legacy_uuid"].strip()
        target = m["target_identifier"].strip()
        action = (m["relation_action"].strip() or "rewrite")
        assert target in ident_to_id, f"canonical target not in seed: {target}"
        canon = ident_to_id[target]
        assert canon in spase_ids, f"canonical target is not a SPASE row: {target}"
        assert action in ("rewrite", "move"), f"unexpected action: {action!r}"
        repoint[legacy] = (canon, action)

    # ---- apply to software.csv ----
    sw_header, sw_rows = read_csv(SOFTWARE)
    s = {name: i for i, name in enumerate(sw_header)}
    ri_i, ro_i = s["related_instruments"], s["related_observatories"]

    touched = 0
    for row in sw_rows:
        ri, ro = uuids(row[ri_i]), uuids(row[ro_i])
        changed = False
        for legacy, (canon, action) in repoint.items():
            if legacy in ri or legacy in ro:
                changed = True
                if action == "rewrite":
                    ri = [canon if x == legacy else x for x in ri]
                    ro = [canon if x == legacy else x for x in ro]
                else:  # move: legacy is an instrument, canonical an observatory
                    ri = [x for x in ri if x != legacy]
                    ro = [x for x in ro if x != legacy] + [canon]
        if changed:
            row[ri_i] = ",".join(dedup(ri))
            row[ro_i] = ",".join(dedup(ro))
            touched += 1

    # ---- references after repointing ----
    referenced = set()
    for row in sw_rows:
        referenced |= set(uuids(row[ri_i])) | set(uuids(row[ro_i]))

    # ---- orphan deletion (unreferenced legacy rows only) ----
    orphan_ids = legacy_ids - referenced
    assert orphan_ids.isdisjoint(apply_no_legacy), (
        f"refusing to delete apply=no legacy rows: {orphan_ids & apply_no_legacy}"
    )
    assert orphan_ids.isdisjoint(referenced), "orphan set intersects referenced set"

    new_io_rows = [r for r in io_rows if r[c["id"]] not in orphan_ids]
    remaining_ids = {r[c["id"]] for r in new_io_rows}

    # safety: every canonical target still exists; no per-cell dup UUIDs
    canon_ids = {canon for canon, _ in repoint.values()}
    assert canon_ids <= remaining_ids, (
        f"canonical targets missing after delete: {canon_ids - remaining_ids}"
    )
    for row in sw_rows:
        for ci in (ri_i, ro_i):
            cell = uuids(row[ci])
            assert len(cell) == len(set(cell)), f"duplicate UUID in cell: {cell}"

    # informational: pre-existing dangling refs in the seed (not introduced here)
    preexisting_dangling = referenced - set(id_to_row)

    # ---- write ----
    write_csv(SOFTWARE, sw_header, sw_rows)
    write_csv(INSTR_OBS, io_header, new_io_rows)

    # ---- summary ----
    print(f"apply=yes mapping rows:       {len(apply_yes)}")
    print(f"  rewrite:                    {sum(1 for _, a in repoint.values() if a == 'rewrite')}")
    print(f"  move:                       {sum(1 for _, a in repoint.values() if a == 'move')}")
    print(f"software rows touched:        {touched}")
    print(f"legacy (non-SPASE) rows:      {len(legacy_ids)} -> {len(legacy_ids) - len(orphan_ids)}")
    print(f"legacy rows deleted (orphan): {len(orphan_ids)}")
    for rid in sorted(orphan_ids, key=lambda x: id_to_row[x][c["name"]].lower()):
        r = id_to_row[rid]
        print(f"   - type={r[c['type']]}  {r[c['name']]!r}  ({rid})")
    print(f"instrument_observatory.csv:   {len(io_rows)} -> {len(new_io_rows)} rows")
    if preexisting_dangling:
        print(f"NOTE: {len(preexisting_dangling)} pre-existing dangling refs in seed (not touched).")


if __name__ == "__main__":
    main()
