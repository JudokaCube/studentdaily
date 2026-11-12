# Arch and AUR packaging

Each app has its own package, command, desktop launcher and optional user service. Installing a package does not change home directories, start services or install the other app. The license is MIT.

The concrete `PKGBUILD` and `.SRCINFO` in this folder target the current GitHub release.

## Local build

From the source folder:

```sh
python3 build-arch.py --version 0.1.0
cd arch-build/studentdaily
makepkg
```

Use the version of the release you intend to build. The output includes the source archive, `PKGBUILD`, `.SRCINFO`, `SHA256SUMS` and `release.json`. `--pkgrel` increments packaging revisions without changing the app version.

## Desktop setup and migration

Run `studentdaily`. Optional integration uses `<app>-setup --bar noctalia` (or `waybar` / `caelestia`). Add `--enable-background` for reminders or scheduled checks. Caelestia needs `--caelestia-root`; restart Waybar/Caelestia after setup.

For an earlier local installation, add `--migrate-local` to point recognized local launchers at the packaged app and remove recognized user-unit overrides. It preserves app data, settings and aliases and refuses unknown launchers. Without migration, old local commands/services may take precedence. Noctalia uses links to the packaged plugin files; rerun setup after upgrades for copied Caelestia integrations.

Uninstall with `pacman -Rns <app>` after disabling its user service and removing its bar entry. Personal data stays in the user's XDG directories.

See [PKGBUILD](https://man.archlinux.org/man/PKGBUILD.5.en), [makepkg](https://man.archlinux.org/man/makepkg.8.en) and [AUR submission guidelines](https://wiki.archlinux.org/title/AUR_submission_guidelines).
