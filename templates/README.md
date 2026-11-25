# Templates

Starting points the Lead copies into the project. Nothing here is used directly by `delegate.py`.

- `roles/ROLE-TEMPLATE.md`: how to make a new worker role (copy to `agent/roles/<name>.md`).
- `notes/`: templates for knowledge notes (system, finding, decision): copy into `knowledge/<kind>s/`.

This is the **cyber** fork: the general-purpose project packs (software, game, research, automation) were removed.
The pentest roles ship directly in `agent/roles/` (recon-analyst, cve-researcher, exploit-builder, executor,
security-reviewer, report-scribe). To add your own role, copy `roles/ROLE-TEMPLATE.md` into `agent/roles/<name>.md`.
