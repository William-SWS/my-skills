# Publishing to GitHub Projects

## Contents

1. Preflight
2. Choosing the repo and the board
3. Dry run, confirm, publish
4. What gets created
5. Reruns and partial failures
6. Troubleshooting

## 1. Preflight

Check these yourself and only hand the user the steps they have to do in person, like logins.

| Check | Command | Fix |
|---|---|---|
| `gh` installed | `gh --version` | Windows: `winget install --id GitHub.cli`. macOS: `brew install gh`. Linux: see cli.github.com. A new terminal may be needed for PATH to update. |
| Logged in | `gh auth status` | The user runs `! gh auth login` (interactive) |
| `project` scope | `gh auth status` lists `project` among the token scopes | The user runs `! gh auth refresh -s project` |
| Repo has a GitHub remote | `git remote -v` / `gh repo view` | Ask which repo the issues belong in |

Installing `gh` changes the user's machine, so ask before running the installer.

## 2. Choosing the repo and the board

- **Repo:** default to the current directory's GitHub repo. If it has several remotes or none, ask.
- **Board:** list candidates with `gh project list --owner <owner>` (`@me` for the user's own, or the org login), and show title, number and URL. If there's exactly one obvious match, recommend it, but still let the user confirm.
- **No board yet:** offer `gh project create --owner <owner> --title "<title>"`. Creating one is an outward-facing action, so confirm first. A new board comes with a `Status` field (`Todo`, `In Progress`, `Done`). Optionally link it to the repo with `gh project link <number> --owner <owner> --repo <owner/name>` so it shows up on the repo's Projects tab.
- **Initial status:** read the options with `gh project field-list <number> --owner <owner> --format json` and ask which column the new cards land in. `Todo` or `Backlog` is the usual answer. A card's `status:` frontmatter overrides that column for one card.
- **Labels:** suggest one shared label such as `feature:<slug>` so the feature's issues can be filtered together. Missing labels are created automatically.

## 3. Dry run, confirm, publish

```bash
python <skill-dir>/scripts/publish_to_github.py docs/features/<slug> \
  --project <number> --owner <owner> --status "Todo" --label "feature:<slug>" --dry-run
```

The dry run validates the cards (unknown blockers, cycles, duplicate ids), the board and the status option, then prints the plan. Show it to the user. It's the last look before anything becomes public in the repo. Run it again without `--dry-run` only after an explicit go-ahead.

Other flags: `--repo owner/name` if the current directory isn't the target repo, `--status-field` if the board's column field isn't called `Status`, and `--no-parent` to publish cards without a parent issue (when the user doesn't want the spec as an issue).

## 4. What gets created

- **Parent issue** from `spec.md`, with the spec as its body and a pointer back to the local file.
- **One issue per card**, created in dependency order, with:
  - its body plus a `## Blocked by` list of `#N` references and a `Part of #parent` line,
  - a native sub-issue link to the parent,
  - native "blocked by" dependencies on its blockers,
  - the card's labels plus any `--label`.
- **Every issue added to the board**, and each card's Status set.
- **`issue: N` written back** into `spec.md` and each card's frontmatter.

## 5. Reruns and partial failures

Each issue number is written to its file right after the issue is created. A rerun skips files that already have `issue:` and only adds them to the board again (a no-op if they're already there). This means:

- A crash or network blip mid-run is fixed by rerunning the same command.
- Adding a new card later works the same way: write `cards/NN-*.md` without `issue:` and rerun. Only the new card is created, and it can be blocked by already-published cards.
- Editing an already-published card's text locally does not update the GitHub issue. Edit it on GitHub, or use `gh issue edit <N> --body-file <file>` when the user asks.

Linking failures (sub-issue, dependency, board) don't abort the run. They're listed under `warnings:` at the end and the script exits with code 2. Relay them to the user and offer to fix each one by hand.

## 6. Troubleshooting

- **`your token has not been granted the required scopes`**: run `gh auth refresh -s project`.
- **Sub-issue or dependency call returns 404/422**: the repo or plan may not have those features enabled, or the link already exists. The `Blocked by` and `Part of` lines in the body still record the relationship, so it's a warning, not a blocker.
- **Org project not found**: pass `--owner <org-login>`. The user also needs write access to the org's project.
- **Status option not found**: the script lists the valid options. Use one of them exactly, or rename the column on the board.
