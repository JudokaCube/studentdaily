# Arch and AUR packaging

Each app has its own package, command, desktop launcher and optional user service. Installing a package does not change home directories, start services or install the other app. The license is MIT.

The concrete `PKGBUILD` and `.SRCINFO` in this folder target the current GitHub release. AUR submission is pending.

## Local build

From the source folder:

```sh
python3 build-arch.py --version 0.1.0
cd arch-build/studentdaily
makepkg
```

Use the version of the release you intend to build. The output includes the source archive, `PKGBUILD`, `.SRCINFO`, `SHA256SUMS` and `release.json`. `--pkgrel` increments packaging revisions without changing the app version.

## Prepare a public release

1. Choose the version and confirm the repository's LICENSE is MIT. Publish only the corresponding public source folder, never files prefixed `PRIVATE`.
2. Run `build-arch.py` with `--version`, `--project-url` and `--source-url`. The source URL must be the future HTTPS release-asset URL for the generated `<app>-<version>.tar.gz`.
3. Upload that exact source archive to the release. Do not substitute GitHub's automatically generated source archive or an installer archive.
4. Rerun the same command with `--verify-source`. It downloads the asset and verifies its SHA-256 checksum against the current source tree. Do not change the source tree between these steps.
5. Build with `makepkg`, inspect with `namcap`, and test in a clean Arch chroot using `extra-x86_64-build` from `devtools`. Confirm the package works in a fresh user account and does not contain personal data.
6. Recheck the package name on the AUR. Submit only `PKGBUILD` and `.SRCINFO` to the matching AUR repository, using an AUR account and SSH key. The builder never publishes or runs Git.

A successful local build is not a substitute for testing a publicly downloadable release. Keep the same source asset immutable after publishing. The AUR handles build recipes; GitHub hosts the app source and release assets.

## Desktop setup and migration

Run `studentdaily`. Optional integration uses `<app>-setup --bar noctalia` (or `waybar` / `caelestia`). Add `--enable-background` for reminders or scheduled checks. Caelestia needs `--caelestia-root`; restart Waybar/Caelestia after setup.

For an earlier local installation, add `--migrate-local` to point recognized local launchers at the packaged app and remove recognized user-unit overrides. It preserves app data, settings and aliases and refuses unknown launchers. Without migration, old local commands/services may take precedence. Noctalia uses links to the packaged plugin files; rerun setup after upgrades for copied Caelestia integrations.

Uninstall with `pacman -Rns <app>` after disabling its user service and removing its bar entry. Personal data stays in the user's XDG directories.

See [PKGBUILD](https://man.archlinux.org/man/PKGBUILD.5.en), [makepkg](https://man.archlinux.org/man/makepkg.8.en) and [AUR submission guidelines](https://wiki.archlinux.org/title/AUR_submission_guidelines).
