#!/usr/bin/env python3
"""Publish a feature folder (spec.md + cards/*.md) to GitHub.

The spec becomes a parent issue, each card becomes an issue linked to it as a
sub-issue, card blockers become native "blocked by" dependencies, and every
issue is added to a GitHub Projects (v2) board with its Status set.

Issue numbers are written back into each file's frontmatter (`issue: N`) as
soon as the issue exists, so a rerun skips what was already published instead
of duplicating it.

Usage:
    python publish_to_github.py docs/features/<slug> --project 3 [--owner @me]
        [--repo owner/name] [--status Todo] [--status-field Status]
        [--label feature:<slug>] [--dry-run]

Needs only the Python standard library and the GitHub CLI (`gh`) logged in
with the `project` scope (`gh auth refresh -s project`).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", re.S)


class GhError(RuntimeError):
    pass


# ---------------------------------------------------------------- files


def parse_value(raw):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [x.strip().strip("'\"") for x in raw[1:-1].split(",") if x.strip()]
    return raw.strip("'\"")


def read_doc(path):
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    m = FRONTMATTER.match(text)
    if m:
        body = m.group(2)
        for line in m.group(1).splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            key, sep, value = line.partition(":")
            if sep:
                meta[key.strip()] = parse_value(value)
    # The issue title carries the heading already; drop a leading H1 from the body.
    heading = re.match(r"\s*#\s+(.+?)\s*(\r?\n|\Z)", body)
    if heading:
        meta.setdefault("title", heading.group(1))
        body = body[heading.end():]
    return meta, body.strip()


def write_field(path, key, value):
    """Set `key: value` in the file's frontmatter, adding the frontmatter if missing."""
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER.match(text)
    if not m:
        text = f"---\n{key}: {value}\n---\n\n{text}"
    else:
        lines = m.group(1).splitlines()
        for i, line in enumerate(lines):
            if line.partition(":")[0].strip() == key:
                lines[i] = f"{key}: {value}"
                break
        else:
            lines.append(f"{key}: {value}")
        text = "---\n" + "\n".join(lines) + "\n---\n" + m.group(2)
    path.write_text(text, encoding="utf-8")


def norm_id(raw):
    raw = str(raw).strip()
    return str(int(raw)) if raw.isdigit() else raw.lower()


def load_cards(cards_dir):
    cards = []
    for path in sorted(cards_dir.glob("*.md")):
        meta, body = read_doc(path)
        raw_id = meta.get("id") or path.stem.split("-", 1)[0]
        blocked = meta.get("blocked_by") or []
        if isinstance(blocked, str):
            blocked = [blocked] if blocked else []
        labels = meta.get("labels") or []
        if isinstance(labels, str):
            labels = [labels] if labels else []
        cards.append({
            "path": path,
            "id": norm_id(raw_id),
            "title": meta.get("title") or path.stem,
            "body": body,
            "blocked_by": [norm_id(b) for b in blocked],
            "labels": labels,
            "status": meta.get("status") or None,
            "issue": int(meta["issue"]) if str(meta.get("issue", "")).isdigit() else None,
        })
    return cards


def dependency_order(cards):
    by_id = {c["id"]: c for c in cards}
    if len(by_id) != len(cards):
        sys.exit("error: two cards share the same id")
    for c in cards:
        for b in c["blocked_by"]:
            if b not in by_id:
                sys.exit(f"error: card {c['id']} is blocked by unknown card {b!r}")
    ordered, state = [], {}

    def visit(c, trail):
        if state.get(c["id"]) == "done":
            return
        if state.get(c["id"]) == "visiting":
            sys.exit("error: blocking cycle: " + " -> ".join(trail + [c["id"]]))
        state[c["id"]] = "visiting"
        for b in c["blocked_by"]:
            visit(by_id[b], trail + [c["id"]])
        state[c["id"]] = "done"
        ordered.append(c)

    for c in cards:
        visit(c, [])
    return ordered


# ---------------------------------------------------------------- gh


def gh(*args):
    env = dict(os.environ, GH_PROMPT_DISABLED="1", NO_COLOR="1")
    proc = subprocess.run(["gh", *args], capture_output=True, text=True,
                          encoding="utf-8", env=env)
    if proc.returncode != 0:
        raise GhError(f"gh {' '.join(args)}\n{proc.stderr.strip() or proc.stdout.strip()}")
    return proc.stdout.strip()


def gh_json(*args):
    return json.loads(gh(*args))


def check_auth():
    if not shutil.which("gh"):
        sys.exit("error: GitHub CLI (gh) not found on PATH. See references/github.md.")
    env = dict(os.environ, GH_PROMPT_DISABLED="1", NO_COLOR="1")
    proc = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True,
                          encoding="utf-8", env=env)
    out = proc.stdout + proc.stderr
    if proc.returncode != 0:
        sys.exit("error: gh is not logged in. Run `gh auth login`.\n" + out)
    if "project" not in out:
        sys.exit("error: gh token lacks the `project` scope. Run `gh auth refresh -s project`.")


def create_issue(repo, title, body, labels):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(body)
        body_path = f.name
    try:
        args = ["issue", "create", "--repo", repo, "--title", title, "--body-file", body_path]
        for label in labels:
            args += ["--label", label]
        url = gh(*args).splitlines()[-1].strip()
    finally:
        os.unlink(body_path)
    return int(url.rstrip("/").rsplit("/", 1)[-1]), url


def issue_db_id(repo, number):
    return int(gh("api", f"repos/{repo}/issues/{number}", "--jq", ".id"))


def project_meta(number, owner, status_field):
    project_id = gh_json("project", "view", str(number), "--owner", owner, "--format", "json")["id"]
    fields = gh_json("project", "field-list", str(number), "--owner", owner,
                     "--format", "json", "--limit", "100")["fields"]
    field = next((f for f in fields if f["name"].lower() == status_field.lower()), None)
    return project_id, field


def option_id(field, name):
    for opt in (field or {}).get("options", []):
        if opt["name"].lower() == name.lower():
            return opt["id"]
    return None


# ---------------------------------------------------------------- main


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("feature_dir", type=Path, help="docs/features/<slug>")
    ap.add_argument("--project", type=int, required=True, help="GitHub Project number")
    ap.add_argument("--owner", help="project owner (user/org login or @me); defaults to the repo owner")
    ap.add_argument("--repo", help="owner/name; defaults to the current directory's repo")
    ap.add_argument("--status", help="Status option for cards without their own `status:`")
    ap.add_argument("--status-field", default="Status", help="name of the single-select status field")
    ap.add_argument("--label", action="append", default=[], help="label added to every issue (repeatable)")
    ap.add_argument("--no-parent", action="store_true", help="don't publish spec.md as a parent issue")
    ap.add_argument("--dry-run", action="store_true", help="print the plan; change nothing on GitHub")
    a = ap.parse_args()

    spec_path = a.feature_dir / "spec.md"
    cards_dir = a.feature_dir / "cards"
    if not cards_dir.is_dir():
        sys.exit(f"error: {cards_dir} not found")
    cards = dependency_order(load_cards(cards_dir))
    if not cards:
        sys.exit(f"error: no cards in {cards_dir}")
    spec = None
    if not a.no_parent:
        if not spec_path.exists():
            sys.exit(f"error: {spec_path} not found (pass --no-parent to publish cards alone)")
        meta, body = read_doc(spec_path)
        spec = {"path": spec_path, "title": meta.get("title") or a.feature_dir.name, "body": body,
                "issue": int(meta["issue"]) if str(meta.get("issue", "")).isdigit() else None}

    gh_ok = bool(shutil.which("gh"))
    if not a.dry_run:
        check_auth()

    repo = a.repo
    if not repo and gh_ok:
        try:
            repo = gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner")
        except GhError as e:
            if not a.dry_run:
                sys.exit(f"error: couldn't detect the repo, pass --repo\n{e}")
    repo = repo or "<repo>"
    owner = a.owner or repo.split("/")[0]

    project_id, field = None, None
    if gh_ok:
        try:
            project_id, field = project_meta(a.project, owner, a.status_field)
        except GhError as e:
            if not a.dry_run:
                sys.exit(f"error: couldn't read project {a.project} of {owner}\n{e}")
            print(f"warning: couldn't read the project (fine for a dry run): {e}\n")

    statuses = {c["status"] or a.status for c in cards} - {None}
    if field is None and statuses and project_id:
        sys.exit(f"error: project has no field named {a.status_field!r}")
    if field:
        missing = [s for s in statuses if not option_id(field, s)]
        if missing:
            names = ", ".join(o["name"] for o in field.get("options", []))
            sys.exit(f"error: status {missing} not in {a.status_field!r} options: {names}")

    # ---- plan
    print(f"repo: {repo}   project: {owner}#{a.project}")
    if spec:
        state = f"#{spec['issue']} (already published)" if spec["issue"] else "new"
        print(f"parent  {spec['title']}  [{state}]")
    for c in cards:
        state = f"#{c['issue']} (already published)" if c["issue"] else "new"
        extra = []
        if c["blocked_by"]:
            extra.append("blocked by " + ", ".join(c["blocked_by"]))
        if c["labels"] or a.label:
            extra.append("labels " + ", ".join(c["labels"] + a.label))
        if c["status"] or a.status:
            extra.append("status " + (c["status"] or a.status))
        print(f"card {c['id']:>3}  {c['title']}  [{state}]" + (f"  ({'; '.join(extra)})" if extra else ""))
    if a.dry_run:
        print("\ndry run: nothing was changed on GitHub")
        return

    # ---- labels
    wanted = sorted({l for c in cards for l in c["labels"]} | set(a.label))
    if wanted:
        existing = {l["name"] for l in gh_json("label", "list", "--repo", repo, "--json", "name", "--limit", "1000")}
        for label in wanted:
            if label not in existing:
                gh("label", "create", label, "--repo", repo)

    warnings, numbers, published = [], {}, []

    # ---- parent issue
    parent = None
    if spec:
        if spec["issue"]:
            parent = spec["issue"]
        else:
            body = spec["body"] + f"\n\n---\nSource: `{spec_path.as_posix()}`"
            parent, _ = create_issue(repo, spec["title"], body, a.label)
            write_field(spec_path, "issue", parent)
            print(f"created parent #{parent}")
        published.append((spec["title"], parent, None))

    # ---- cards, blockers first
    for c in cards:
        if c["issue"]:
            numbers[c["id"]] = c["issue"]
            published.append((c["title"], c["issue"], c["status"] or a.status))
            continue
        body = c["body"]
        if c["blocked_by"]:
            body += "\n\n## Blocked by\n\n" + "\n".join(f"- #{numbers[b]}" for b in c["blocked_by"])
        if parent:
            body += f"\n\nPart of #{parent}"
        number, _ = create_issue(repo, c["title"], body, c["labels"] + a.label)
        write_field(c["path"], "issue", number)
        numbers[c["id"]] = number
        published.append((c["title"], number, c["status"] or a.status))
        print(f"created card {c['id']} as #{number}")

        db_id = issue_db_id(repo, number)
        if parent:
            try:
                gh("api", "-X", "POST", f"repos/{repo}/issues/{parent}/sub_issues", "-F", f"sub_issue_id={db_id}")
            except GhError as e:
                warnings.append(f"#{number} not linked as sub-issue of #{parent}: {e}")
        for b in c["blocked_by"]:
            try:
                gh("api", "-X", "POST", f"repos/{repo}/issues/{number}/dependencies/blocked_by",
                   "-F", f"issue_id={issue_db_id(repo, numbers[b])}")
            except GhError as e:
                warnings.append(f"#{number} not marked blocked by #{numbers[b]} (the body still says so): {e}")

    # ---- project board
    for title, number, status in published:
        url = f"https://github.com/{repo}/issues/{number}"
        try:
            item = gh_json("project", "item-add", str(a.project), "--owner", owner, "--url", url, "--format", "json")
            if status:
                gh("project", "item-edit", "--id", item["id"], "--project-id", project_id,
                   "--field-id", field["id"], "--single-select-option-id", option_id(field, status))
        except GhError as e:
            warnings.append(f"#{number} not added to the project or its status not set: {e}")

    print("\npublished:")
    for title, number, status in published:
        print(f"  #{number}  {title}" + (f"  [{status}]" if status else ""))
        print(f"        https://github.com/{repo}/issues/{number}")
    if warnings:
        print("\nwarnings:")
        for w in warnings:
            print("  - " + w.replace("\n", "\n    "))
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except GhError as e:
        sys.exit(f"error: {e}")
