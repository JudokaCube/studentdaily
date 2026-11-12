# StudentDaily

Organize classes, personal events and daily tasks, with reminders and a desktop widget.

## Features

- Classes and personal events, with interactive forms and edits for one occurrence, future occurrences or the whole series.
- Daily School/Life tasks, teachers, meeting links, extra timezone clocks and search.
- Event reminders, progress indicators, early finish/undo, and JSON import/export.
- Nine themes, optional transparency, square border styles and configurable widgets.

## Installation

Requires Linux, Python 3.11+, Kitty and systemd. Reminders use python-dbus and python-gobject.

Download the installer from [GitHub Releases](https://github.com/JudokaCube/studentdaily/releases/latest), extract it, and run `bash install.sh`. The installer starts with no personal data.

From the source folder:

```sh
python3 build-release.py
bash release/install.sh
```

For an extracted installer archive, run `bash install.sh` instead.

This installer includes only StudentDaily and its widgets. Choose a bar, theme and background-service options during setup. Existing app data is preserved. Open a new terminal to use newly enabled aliases.

## Usage

Run `studentdaily`. Local installs also provide `classes`, with optional `class` and `today` aliases. Use **Schedule** to add or edit events, **Zones** for clocks, and **Data** for import/export. Click controls or use the keyboard; **H** opens help.

In event forms, type directly into fields, use arrows or Tab to move, and toggle repeat days with Space. **Apply to** opens the one-date, future-date and entire-series choices; a summary shows the affected dates. Weekly presets select weekdays or daily personal events. **Ctrl+S** saves; **Esc** cancels. Personal events have no teacher or meeting-link fields. Clocks use city search, and tasks and import/export use selectable menus instead of numbered prompts.

## Settings

Open **Settings** or press **Y**. Use arrows for quick adjustments; Enter or a click opens choices. Theme colors and square borders preview in Settings while preserving terminal transparency. **Save / Ctrl+S** applies changes; **Esc** discards unsaved changes. **Defaults** selects the default values; Save applies them.

- StudentDaily: 12/24-hour clocks, clock seconds, week numbers, teacher details, default event length, reminders, progress, weekends and task summary.
- Appearance: theme, opacity, borders, widget visibility and text. Noctalia also supports animation controls.

Widget settings take effect on the next poll. Opacity applies to newly launched windows. Settings belong only to this app.

## Desktop bars

- **Noctalia 5.3+**: native widgets with hover details.
- **Waybar**: custom modules and tooltips. Restart Waybar after installation. JSONC values are preserved; formatting and comments are rewritten.
- **Caelestia**: requires a writable shell checkout using `--caelestia-root`. The installer adds a QML component; restart the shell afterward. This integration has syntax/integration checks but has not been visually tested in a running Caelestia session.
- **No bar**: use the apps and optional background services on their own.

Right-click a widget to reload and open its app.

## Arch packaging

Separate Arch package builds are available through `build-arch.py`. See [Arch packaging](packaging/aur/README.md) for local builds and future AUR release preparation. AUR submission is pending; the release source can already be built locally with `makepkg`.

## License

MIT · jdkcube
