# StudentDaily

Organize classes, personal events and daily tasks, with reminders and a desktop widget.

## Features

- Classes and personal events, with interactive forms and edits for one occurrence, future occurrences or the whole series.
- Daily School/Life tasks, teachers, meeting links, extra timezone clocks and search.
- Event reminders, progress indicators, early finish/undo, and JSON import/export.
- Nine themes, optional transparency, square border styles and configurable widgets.

## Installation

Requires Linux, Python 3.11+, Kitty and systemd. Reminders use python-dbus and python-gobject.

Download the installer archive from [GitHub Releases](https://github.com/JudokaCube/studentdaily/releases/latest) and extract it.

From the installer folder, run as your normal desktop user:

```sh
bash install.sh
```

This installer includes only StudentDaily and its widgets. Choose a bar, theme and background-service options during setup. Existing app data is preserved. Open a new terminal to use newly enabled aliases.

## Usage

Run `studentdaily`. Local installs also provide `classes`, with optional `class` and `today` aliases. Use **Schedule** to add or edit events, **Zones** for clocks, and **Data** for import/export. Click controls or use the keyboard; **H** opens help.

In event forms, type directly into fields, use arrows or Tab to move, and toggle repeat days with Space. **Apply to** opens the one-date, future-date and entire-series choices; a summary shows the affected dates. Weekly presets select weekdays or daily personal events. **Ctrl+S** saves; **Esc** cancels. In **To-do**, choose **Plan tasks** (P) to reschedule a task, change its category or bring earlier unfinished tasks onto the selected date. When saving a changed meeting link, choose all classes with that title or the selected event scope. Personal events have no teacher or meeting-link fields.

## Settings

Open **Settings** or press **Y**. Use arrows for quick adjustments; Enter or a click opens choices. **Save / Ctrl+S** applies changes; **Esc** discards unsaved changes.

- StudentDaily: 12/24-hour clocks, clock seconds, week numbers, teacher details, default event length, reminders, progress, weekends and task summary.
- Appearance: theme, opacity, borders, widget visibility and text. Noctalia also supports animation controls.

Reopen the app after changing opacity. Widget changes appear after a short delay.

## Desktop bars

- **Noctalia 5.3+**: native widgets with hover details.
- **Waybar**: custom modules and tooltips. Restart Waybar after installation.
- **Caelestia**: requires a writable shell checkout using `--caelestia-root`. Restart the shell after installation.
- **No bar**: use the apps and optional background services on their own.

Right-click a widget to reload and open its app.

## License

MIT · jdkcube
