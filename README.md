# StudentDaily

Customizable terminal app and desktop widget. MIT licensed. Public releases start without personal data.

## Install

Requires Linux, Python 3.11+, Kitty and systemd. Reminders use python-dbus and python-gobject.

```sh
python3 build-release.py
bash release/install.sh
```

For a downloaded installer, run `bash install.sh`. Setup offers theme, opacity, bar, position, aliases and reminders. Existing data is preserved; no keybindings are added. `--help` lists flags; `--yes` uses defaults/flags without questions.

## Bars

- Noctalia 5.3+: native plugins, enabled automatically.
- Waybar: native custom modules; existing JSON/JSONC values are preserved, formatting/comments are rewritten. Restart Waybar after installation.
- Caelestia: requires an editable shell checkout via `--caelestia-root`; setup adds the supplied QML widget to its bar. Restart that shell afterward. System-owned files are not changed.
- None: apps and optional background services only.

Right-click opens fresh app code. Widget styles follow the shared theme. Waybar uses tooltips for hover details; Caelestia uses a tooltip and progress strip. Shell-native notification alignment remains controlled by the shell.

## StudentDaily

Run `classes` or `python3 bin/classes`. Click controls; arrows/wheel scroll; Tab selects.

- Schedule: subjects, teachers, times, Zoom links, and once/future/all edits.
- Zones: add, edit, remove extra clocks; class times stay local.
- Search: classes, teachers and tasks.
- Data: export/import schedule, teachers, links, tasks, clocks, completion and theme; merge or replace.
- Finish (m): end today’s selected class early; press again to undo.
- To-do: daily school/life tasks; h lists all controls.

Week view is Monday–Friday. Reminders and progress follow today’s unfinished classes. Setup offers empty, customize now, or private preset import. Exports contain meeting links; keep private data off GitHub.

## Appearance and development

Open theme/appearance for nine palettes. Arrows preview, Enter/click saves, Esc cancels, n resets Nord. Opacity defaults to 94%. Reopen windows after code or launch-setting changes. Settings respect XDG directories; runtime data stays outside the source tree.

`bin/` apps, `plugins/` Noctalia widgets, `integrations/` other bars, `services/` startup, `packaging/` installer.

```sh
noctalia plugins lint plugins/*
python3 build-release.py
```

Rebuild after edits. Upload this source folder, including `.gitignore`, and attach `release.tar.gz` to releases. Files starting `PRIVATE-` are personal copies, not public releases.
