# studentdaily

customizable terminal apps and desktop widgets. mit licensed. public releases start without personal data.

## install

requires linux, python 3.11+, kitty and systemd. packages uses arch/pacman, flatpak and checkupdates or fakeroot; yay/paru adds aur. reminders use python-dbus and python-gobject.

```sh
python3 build-release.py
bash release/install.sh
```

for a downloaded installer, run `bash install.sh`. setup offers apps, theme, opacity, bar, position, aliases, reminders, check interval and package confirmations. existing data is preserved; no keybindings are added. `--help` lists flags; `--yes` uses defaults/flags without questions.

## bars

- noctalia 5.3+: native plugins, enabled automatically
- waybar: native custom modules; existing json/jsonc values are preserved, formatting/comments are rewritten. restart waybar after installation
- caelestia: requires an editable shell checkout via `--caelestia-root`; setup adds the supplied qml widget to its bar. restart that shell afterward. system-owned files are not changed
- none: apps and optional background services only

right-click opens fresh app code. widget styles follow the shared theme. waybar uses tooltips for hover details; caelestia uses a tooltip and progress strip. shell-native notification alignment remains controlled by the shell.

## studentdaily

run `classes` or `python3 bin/classes`. click controls; arrows/wheel scroll; tab selects.

- schedule: subjects, teachers, times, zoom links, and once/future/all edits
- zones: add, edit, remove extra clocks; class times stay local
- search: classes, teachers and tasks
- data: export/import schedule, teachers, links, tasks, clocks, completion and theme; merge or replace
- finish (m): end today’s selected class early; press again to undo
- to-do: daily school/life tasks; h lists all controls

week view is monday–friday. reminders and progress follow today’s unfinished classes. setup offers empty, customize now, or private preset import. exports contain meeting links; keep private data off github.

## appearance and development

open theme/appearance for nine palettes. arrows preview, enter/click saves, esc cancels, n resets nord. opacity defaults to 94%. reopen windows after code or launch-setting changes. settings respect xdg directories under `classes` and `nord-desktop`; runtime data stays outside the source tree.

`bin/` apps, `plugins/` noctalia widgets, `integrations/` other bars, `services/` startup, `packaging/` installer.

```sh
noctalia plugins lint plugins/*
python3 build-release.py
```

rebuild after edits. upload this source folder, including `.gitignore`, and attach `release.tar.gz` to releases. files starting `private-` are personal copies, not public releases.
