# Menubarn Installer — plan

Status: **planned, not started** (2026-09-09). Nothing here is built. The
blocking work is administrative (Apple Developer Program, Developer ID
signing, notarization), so this document exists to make the eventual build a
matter of execution rather than design.

## Goal

A single download that lets a non-technical Mac user pick which Menubarn
widgets they want — **all ten selected by default** — and installs them with
no Terminal, no Xcode, no `git clone`. Today every app is installed by
building from source with `install.sh`, which rules out most of the people the
site is written for.

## What the user experiences

1. Download `Menubarn.dmg` from widgets.nicksmith.software (one button on the
   hero, one on every app page). Open it, drag **Menubarn Installer** to
   Applications, open it. Gatekeeper lets it run without a warning because it
   is Developer ID signed and notarized.
2. A single window: the barn mascot, a short line, and a checklist of the ten
   widgets. Each row shows the mascot, the name, the one-line blurb from the
   site, and its menu-bar glyph strip. Every row is checked. A footer shows
   "10 of 10 selected · 18 MB" and an **Install** button.
3. Install runs in place: rows tick through "Downloading → Installing → Done".
   Apps land in `~/Applications` (no admin password) and launch. A final screen
   lists what was installed, which ones need a permission (KeyLight, Curtain
   and MacRecorder need Accessibility or Screen Recording) with a button that
   opens the right System Settings pane, and a **Start at Login for all**
   toggle.
4. Re-opening the installer later shows installed versions, offers updates,
   and lets the user add or remove widgets. Removal quits the app, unregisters
   Start at Login, and moves the bundle to the Trash.

## Approach

**A native SwiftUI installer app that downloads notarized builds from GitHub
Releases.** Considered and rejected:

- *A `.pkg` with an Installer.app choices pane.* Free of any new code, but the
  choices UI is ugly, cannot show mascots or glyphs, needs an admin password,
  and cannot offer updates or removal afterwards.
- *A Homebrew tap (`brew install --cask nicholaspsmith/menubarn/keylight`).*
  Worth doing anyway for the technical audience, but it is not the
  non-technical path and still needs signed builds to avoid Gatekeeper
  prompts.
- *Mac App Store.* The apps depend on things the sandbox forbids (CGEventTap,
  private CoreBrightness, AX access to other apps' menu bars, signalling other
  processes). Not viable for most of the ten.

The installer itself is a StatusItemKit-free SwiftUI app (a normal windowed
app, not a menu-bar one), Developer ID signed and notarized, shipped in a DMG.

## Prerequisites (the administrative part)

| Step | Notes |
|------|-------|
| Apple Developer Program membership | $99/yr, individual is fine. Needed for a Developer ID certificate; without it every app triggers "cannot be opened because the developer cannot be verified". |
| Developer ID Application certificate | Created in the developer portal, installed in the login keychain on the build Mac (and exported as a `.p12` for CI). Replaces the self-signed "StatusItemKit Local Signing" identity for release builds only; local builds keep the self-signed identity so TCC grants stay stable during development. |
| Notarization credentials | An app-specific password for `notarytool`, stored in the keychain (`xcrun notarytool store-credentials`) and as a CI secret. |
| Team ID + bundle identifiers | Every app already has a `com.nicholaspsmith.*` bundle id; record the Team ID in one place (`StatusItemKit/scripts/release.env`). |
| Hardened runtime entitlements | Required for notarization. Audit each app for what it needs: KeyLight/MacRecorder/Apollo (CGEventTap) need no special entitlement but must not be sandboxed; MacRecorder needs `com.apple.security.device.audio-input`? (no — ScreenCaptureKit system audio does not) — verify per app during the first notarization run. |

Nothing else in this plan can start until the certificate exists.

## Release pipeline (per app)

Add to `StatusItemKit/scripts/`:

- `release-app.sh <repo>` — builds with `make-app.sh` using the Developer ID
  identity and hardened runtime, `codesign --timestamp --options runtime`,
  zips with `ditto -c -k --keepParent`, submits with `notarytool submit --wait`,
  staples, and writes `<App>-<version>.zip` plus a `sha256`.
- Versioning: `CFBundleShortVersionString` from a git tag `v1.2.3` in each
  repo; `CFBundleVersion` = commit count. `make-app.sh` already writes
  Info.plist, so this is a small extension.
- GitHub Actions workflow (one reusable workflow in StatusItemKit, called by
  each app repo on tag push): macOS runner, import the `.p12` and notary
  credentials from secrets, run `release-app.sh`, create a GitHub Release with
  the zip and checksum.
- A **manifest** the installer reads: `https://widgets.nicksmith.software/releases/manifest.json`,
  regenerated by a script in this repo from the GitHub Releases API:

  ```json
  {
    "generated": "2026-10-01T12:00:00Z",
    "apps": [
      { "id": "keylight", "name": "KeyLight", "bundleId": "com.nicholaspsmith.KeyLight",
        "version": "1.2.0", "size": 1834221,
        "url": "https://github.com/nicholaspsmith/keylight-menubar/releases/download/v1.2.0/KeyLight-1.2.0.zip",
        "sha256": "…", "minOS": "13.0",
        "permissions": ["accessibility"],
        "blurb": "Remaps Ctrl + the brightness keys…",
        "mascot": "https://widgets.nicksmith.software/img/mascots/keylight.png",
        "glyphs": "https://widgets.nicksmith.software/img/glyphs/keylight.png" }
    ]
  }
  ```

  The manifest is the single source of truth for the installer's list; the
  site's `build-pages.py` and the manifest generator should read the same
  `apps.json` so the blurbs never drift.

## The installer app

Repo: `~/Code/menubarn-installer` (public, MIT, like the rest).

- **Targets:** macOS 13+, SwiftUI, one window, no menu-bar item.
- **Model:** `Manifest` (decoded from the URL above, cached with an ETag),
  `InstalledApp` (found by scanning `~/Applications` and `/Applications` for
  the known bundle ids via `NSWorkspace.urlForApplication(withBundleIdentifier:)`
  and reading their versions), `InstallPlan` (selected ids minus already
  current).
- **Screens:** Welcome/checklist → Progress → Done/Permissions. A fourth
  "Manage" view is the same checklist with Installed/Update/Remove states,
  shown when at least one widget is already installed.
- **Install step per app:** download zip to a temp dir → verify sha256 →
  `ditto -x -k` → verify `codesign --verify --deep --strict` and
  `spctl --assess` pass (refuse otherwise) → quit the running copy if any
  (`NSRunningApplication.terminate`, wait, then `forceTerminate`) → move into
  `~/Applications` (replace atomically via `FileManager.replaceItemAt`) →
  `NSWorkspace.openApplication`. No admin rights needed because nothing goes
  under `/Applications`; offer `/Applications` as an option with an
  `SMJobBless`-free approach (just an authorization prompt via
  `NSWorkspace`'s `requestAuthorization(to: .replaceFile)`).
- **Start at Login for all:** each app registers itself with `SMAppService`
  from its own menu. The installer cannot register them on their behalf, so
  it launches each app with a `--start-at-login` argument that the apps
  honour (a small StatusItemKit addition: `LoginItem.enableIfRequested()`).
- **Permissions screen:** for each installed app that needs a grant, a row
  with the app's mascot, a sentence in plain English ("KeyLight needs
  Accessibility so it can hear the brightness keys"), and a button that opens
  `x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility`
  (or `_ScreenCapture`). Curtain's Accessibility need is optional (Manage
  Icons only); say so.
- **Updates:** the installer compares manifest versions with installed
  versions. Sparkle in every app is deliberately *not* part of phase 1; the
  installer is the updater. (Sparkle can come later if people want in-app
  updates.)
- **Removal:** quit → `SMAppService.unregister` is per-app, so ask the app to
  do it via a `--unregister-login` launch argument before trashing it →
  `FileManager.trashItem`. Preferences in `~/Library/Preferences` are left
  alone unless the user ticks "also remove settings".
- **Telemetry:** none. The only network calls are the manifest and the
  release zips.

## Distribution

- `Menubarn Installer.app` built, signed with Developer ID, hardened runtime,
  notarized, stapled, packed into `Menubarn.dmg` (`create-dmg` with the barn
  scene as the background).
- The DMG is a GitHub Release on `menubarn-installer`; the site links to the
  `latest` release URL. `build-pages.py` gains a "Download the installer"
  button on the hero and each app page, and each app page's Install section
  is rewritten for non-technical users: "Open the Menubarn Installer and tick
  KeyLight" first, then the source route as a collapsed "Build it yourself"
  details block.
- The installer updates itself: it checks its own release tag on launch and
  offers to download the new DMG.

## Phases

1. **Admin (Nick):** join the Developer Program, create the Developer ID
   certificate, store notary credentials, record the Team ID. Nothing else
   starts before this.
2. **Signed builds:** `release-app.sh`, hardened-runtime audit, tag and
   notarize one app (KeyLight) end to end by hand. Confirm a fresh Mac opens
   it with no Gatekeeper warning.
3. **CI:** the reusable GitHub Actions workflow; tag all ten apps and
   StatusItemKit; publish the manifest; wire `--start-at-login` and
   `--unregister-login` into StatusItemKit's `LoginItem`.
4. **Installer app:** checklist → install → permissions, against the real
   manifest. Test on a clean user account and on a Mac with no Xcode.
5. **Manage/updates/removal**, DMG, self-update, site buttons, rewrite of the
   Install sections. Announce.

Rough effort after phase 1: two to three focused days for phases 2–3, three
to four for phases 4–5.

## Open questions

- `~/Applications` vs `/Applications`: default to `~/Applications` (no
  password, and it is where the apps already live on Nick's machine), offer
  `/Applications` as an option?
- Should the installer also offer StatusItemKit/HotkeyKit? No — they are
  libraries; the installer is for the ten apps only.
- Do any of the apps break under the hardened runtime? KeyLight's private
  CoreBrightness use and MacRecorder's ScreenCaptureKit should be fine, but
  the first notarization run in phase 2 is where that gets settled.
- Homebrew cask tap as a parallel technical path: yes, cheap once signed zips
  exist; a separate small plan.
