#!/usr/bin/env python3
"""The Funniest Out-of-Office — make.fun entry.

Writes one line, at most 140 characters, to $MAKEFUN_OUTPUT_DIR/entry.txt
(or ./output/entry.txt when the harness sets no directory): a single-line
out-of-office auto-reply.

The joke: the sender dutifully points urgent mail at their replacement,
then undercuts the whole gesture — the replacement left first. It reads
like a real auto-reply (date, escalation path, polite voice) until the
last clause flips it, and every word is load-bearing: cut "urgent" and
there is no escalation to undercut; cut "before I did" and there is no
twist. No beach, no fishing, no "finding myself" — the inbox clichés
everyone has already read a thousand times are left out on purpose.

The line is assembled from three semantic parts so the setup, the
escalation and the twist stay separately editable, and a normaliser
guarantees the assembled line is exactly one clean line before the
gate checks run. After writing, the file on disk is read back and
validated again, so a partial write or an encoding slip can never
silently ship an entry the judge would never see.
"""

import argparse
import os
import sys

SETUP = "Out of office until Monday."
ESCALATION = "For anything urgent, please contact my replacement,"
TWIST = "who left before I did."

MAX_CHARS = 140


def render():
    """Assemble the entry from its parts and collapse any accidental
    double spacing, so the shipped line is one clean single line."""
    parts = [SETUP, ESCALATION, TWIST]
    text = " ".join(part.strip() for part in parts)
    return " ".join(text.split())


def resolve_output_dir():
    """Where the harness wants the artifact: env override, else ./output."""
    return os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "output"
    )


def validate(text):
    """Mirror the sealed gate, plus the byte and edge checks the gate
    implies: UTF-8 text, 1 to 140 chars, not only whitespace, a single
    line, no leading or trailing space, and no hidden multi-byte
    surprise — fail loudly instead of shipping an entry the judge
    would never see."""
    if not isinstance(text, str):
        raise SystemExit("entry must be text")
    if not text.strip():
        raise SystemExit("entry is empty or only whitespace")
    if text != text.strip():
        raise SystemExit("entry has leading or trailing whitespace")
    if "\n" in text or "\r" in text:
        raise SystemExit("entry must be one line")
    if len(text) > MAX_CHARS:
        raise SystemExit(f"entry is {len(text)} chars, over the {MAX_CHARS} cap")
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_CHARS:
        raise SystemExit(f"entry is {len(encoded)} bytes, over the {MAX_CHARS} cap")


def verify_written(out_path, expected):
    """Read the file back from disk and run the full gate validation
    on what is actually there, not just on what was meant to be
    written."""
    with open(out_path, "rb") as f:
        written = f.read()
    if written != expected.encode("utf-8"):
        raise SystemExit("read-back mismatch: entry.txt does not match the entry")
    validate(written.decode("utf-8"))
    return len(written)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Write the out-of-office entry.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the entry without writing entry.txt.",
    )
    args = parser.parse_args(argv)
    entry_text = render()
    validate(entry_text)
    if args.check:
        print(f"entry valid ({len(entry_text)} chars): {entry_text}")
        return 0
    out_dir = resolve_output_dir()
    out_path = os.path.join(out_dir, "entry.txt")
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write(entry_text)
    n_bytes = verify_written(out_path, entry_text)
    print(f"wrote {out_path} ({len(entry_text)} chars, {n_bytes} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
