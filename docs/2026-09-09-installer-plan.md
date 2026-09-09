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
   lists what was installed, which ones need a permission (KeyLight, Barn
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

## Mac App Store: deliberately not part of this plan

Two separate reasons, either of which is enough on its own.

1. **The widgets cannot be sandboxed.** App Store apps must run in the App
   Sandbox. KeyLight, MacRecorder and Apollo Monitor own a `CGEventTap`;
   KeyLight loads the private CoreBrightness framework; Barn reads other
   apps' menu-bar items over the Accessibility API and drags them; Media
   Tracking Killer sends signals to system daemons; Process Monitor reads
   `sysctl` and other users' process tables; VPN & DNS shells out to the
   `mullvad` and `tailscale` CLIs. Every one of those is blocked or
   review-rejected under the sandbox (guideline 2.4.5 and the entitlement
   list). Battery Time and Download Recycler could probably be made to fit,
   but a two-app store listing is not the product.
2. **The installer cannot be an App Store app.** Guideline 2.4.5(ii) forbids
   apps that download or install other executable code, and the sandbox
   would not let it write into `~/Applications` anyway. An App Store
   "Menubarn" could only be a catalogue that opens the website.

So the distribution path is Developer ID + notarization, which is Apple's
supported route for exactly this kind of software (menu-bar utilities that
need Accessibility or Screen Recording are almost all distributed this way).
If a store presence ever matters for discoverability, the honest option is a
sandboxed subset (Battery Time, Download Recycler) as separate listings, with
the rest still coming from the installer — a later decision, not part of this
plan.

### A free App Store tier, with the rest outside it?

Asked 2026-09-09. Partly workable, with two hard constraints from the review
guidelines that shape what it can be:

**What can go in the store.** Only widgets that work inside the App Sandbox
and touch nothing the sandbox forbids:

| Widget | Sandbox verdict |
|--------|-----------------|
| Battery Time | Yes — `pmset`/IOKit reads are fine; the energy-mode toggle (needs `sudo pmset`) has to go. |
| Download Recycler | Yes — with the `com.apple.security.files.downloads.read-write` entitlement; trashing works. |
| Process Monitor | Probably — `sysctl` and the process table are readable; notifications are fine. Confirm the child-spawner scan in a sandboxed build. |
| Claude Usage | Doubtful — it reads another app's Keychain item and `~/.claude` transcripts. Would need the user to grant folder access via an open panel, and the OAuth token path is out. |
| KeyLight, MacRecorder, Apollo Monitor | No — `CGEventTap` and (KeyLight) a private framework. |
| Barn | No — Accessibility access to other apps' status items. |
| VPN & DNS | No — shells out to the VPN CLIs and toggles system DNS. |
| Media Tracking Killer | No — signals system daemons. |

So a store listing is three widgets, four at a stretch. The natural shape is
**one App Store app, "Menubarn", that hosts those widgets as togglable status
items** in a single binary, rather than three separate listings. Free.

**What the store app may not do.** Two guidelines bite:

- 2.4.5 (and 2.5.2): the store app cannot download, install, or launch code
  from outside, so it cannot be the installer for the rest.
- 3.1.1 / 3.1.3: if the outside set is sold, the store app may not link to or
  mention that purchase — everything a store app *unlocks or upsells* must go
  through in-app purchase, and "steering" users to an outside purchase is a
  rejection. If the outside set is free, a low-key "More widgets at
  widgets.nicksmith.software" link is normally accepted as informational, as
  long as the app is not a storefront for them.

Which means the word **"Premium" is the problem, not the idea**. A free store
tier plus a free Developer ID installer for the full set, with a modest link
between them, is fine. A free store tier that upsells a paid outside tier is
not — the only compliant way to charge is IAP inside the store app for things
the store app itself does, or charging on the website without the store app
ever pointing at it.

**What it costs.** Real App Review (a human, one to three days per
submission, and again for every update); a separate sandboxed build target
with its own bundle id per widget (a bundle id cannot live both inside and
outside the store, and TCC grants and defaults do not carry across); App
Store screenshots, description, privacy "nutrition label", and a privacy
manifest; and the sandbox rework itself (Battery Time loses its energy-mode
toggle, Claude Usage loses its token path). Roughly a week on top of the
installer, most of it the sandbox work and review round-trips.

**Recommendation:** ship the Developer ID installer first (this plan), then
decide on a free three-widget "Menubarn" store app as a discoverability
funnel. Keep both tiers free, name the outside set "the full set", not
"Premium", and let the store app carry one informational link to the site.

## AI-assisted development and Apple review

There is no Apple rule against AI-assisted or AI-generated code, and no risk
of rejection on that basis in either path:

- **Notarization** is an automated scan for malware and for signing and
  hardened-runtime problems. It does not look at source, authorship, or
  tooling, and there is no human reviewer.
- **App Store Review** (not used here, see above) evaluates the running
  binary, its metadata, and guideline compliance. The App Store Review
  Guidelines mention AI only where an app *generates content for users*
  (1.2 user-generated content, 5.1.2 data use), and Apple does not ask how
  the code was written. Plenty of shipping apps are built with Xcode's own
  AI assistance.

What Apple does hold the developer responsible for is the behaviour of the
binary: entitlements, permission use, network use, and honest descriptions.
That is a normal pre-release review, not an authorship review, and it is
already in phase 2 as the hardened-runtime and Info.plist audit. Worth adding
as an explicit checklist item before the first public release, because the
installer downloads and replaces apps and should be read by a human end to
end for that reason alone:

- Read every network call and every file operation in the installer; confirm
  it only ever writes under `~/Applications` (or the chosen folder) and only
  bundles it verified.
- Confirm no app phones home, and say so on the site.
- Confirm each Info.plist usage string matches what the app actually does.

## Prerequisites (the administrative part)

| Step | Notes |
|------|-------|
| Apple Developer Program membership | $99/yr, individual is fine. Needed for a Developer ID certificate; without it every app triggers "cannot be opened because the developer cannot be verified". |
| Developer ID Application certificate | Created in the developer portal, installed in the login keychain on the build Mac (and exported as a `.p12` for CI). Replaces the self-signed "StatusItemKit Local Signing" identity for release builds only; local builds keep the self-signed identity so TCC grants stay stable during development. |
| Notarization credentials | An app-specific password for `notarytool`, stored in the keychain (`xcrun notarytool store-credentials`) and as a CI secret. |
| Team ID + bundle identifiers | Every app already has a `com.nicholaspsmith.*` bundle id; record the Team ID in one place (`StatusItemKit/scripts/release.env`). |
| Hardened runtime entitlements | Required for notarization. Audit each app for what it needs: KeyLight/MacRecorder/Apollo (CGEventTap) need no special entitlement but must not be sandboxed; MacRecorder needs `com.apple.security.device.audio-input`? (no — ScreenCaptureKit system audio does not) — verify per app during the first notarization run. |

Nothing else in this plan can start until the certificate exists.

## Apple gotchas checklist

Things that are not obvious until they bite. Each one is a known step, not a
risk, as long as it is on the list.

**Accounts and agreements**
- There is **no App Review** for Developer ID distribution. "Approval" here
  means notarization: an automated malware scan that usually returns in
  minutes. It can still reject a build (unsigned nested code, no hardened
  runtime, no secure timestamp), and the rejection reasons only appear in
  `notarytool log`, not in the submit output.
- Notarization fails with "You must first sign the relevant contracts" until
  the Program License Agreement is accepted in App Store Connect — and it has
  to be re-accepted every time Apple revises it, which silently breaks CI.
- The `notarytool` app-specific password needs two-factor authentication on
  the Apple ID. Alternatively an App Store Connect API key (issuer id, key
  id, `.p8`), which is the better fit for CI.
- Developer ID certificates last five years; the membership is yearly. If
  the membership lapses, existing signed builds keep running but nothing new
  can be signed or notarized.
- Only the **Developer ID Application** certificate is needed. Developer ID
  Installer is for `.pkg` files, which this plan does not use.

**Signing**
- Every Mach-O in the bundle must be signed with the same identity, inside
  out (helpers, then the app), with `--timestamp` and `--options runtime`.
  SwiftPM executables are single binaries, so this is one `codesign` per app,
  but the installer must also sign anything it embeds (e.g. a bundled
  `create-dmg` background is fine, a helper tool is not unless signed).
- Hardened runtime turns on **library validation**: the app may only load
  libraries signed by Apple or by the same Team ID. CoreBrightness (KeyLight)
  is Apple-signed, so it loads; anything third-party would need the
  `disable-library-validation` entitlement, which notarization allows but
  weakens the story. Audit each app the first time.
- Entitlements the apps actually need are few: none of them use the sandbox,
  so `com.apple.security.app-sandbox` must stay off. MacRecorder captures
  system audio through ScreenCaptureKit, which is a TCC permission (Screen
  Recording), not an entitlement.
- The ad-hoc/self-signed identity used for local builds ("StatusItemKit
  Local Signing") and the Developer ID identity produce different code
  signatures, so **switching a running app to a Developer ID build resets
  its TCC grants once** on that Mac. Afterwards, Developer ID grants persist
  across updates because TCC keys on the designated requirement (Team ID +
  bundle id), not on the cdhash.
- Universal binaries: build `-arch arm64 -arch x86_64` or state Apple Silicon
  only. macOS 13 still runs on Intel Macs, so the honest default is universal;
  it roughly doubles binary size, which is trivial here.

**Notarization and Gatekeeper**
- **Staple** the ticket to every app (`xcrun stapler staple`) *and* to the
  DMG. An unstapled app still passes, but only if the Mac can reach Apple at
  first launch; stapled ones pass offline.
- Verify with both `codesign --verify --deep --strict` and
  `spctl --assess --type execute` before publishing; the installer should run
  the same two checks on every zip it downloads and refuse anything that
  fails.
- Downloads get the quarantine attribute. That is correct and must not be
  stripped by the installer; a notarized, stapled app launches cleanly with
  it. A build that is only signed, or only notarized without stapling on an
  offline Mac, shows "cannot be opened because the developer cannot be
  verified" — that message is the test that phase 2 has actually succeeded.
- **App Translocation:** a quarantined app launched straight from a DMG (or
  from the Downloads folder next to other files) runs from a randomised
  read-only path. SMAppService registration and self-update both misbehave
  there, so the DMG must make the "drag to Applications" step unavoidable and
  the installer should refuse to run translocated
  (`SecTranslocateIsTranslocatedURL`) and explain why.
- macOS 15 removed "Allow applications from anywhere" and the Control-click
  Open shortcut for unsigned apps; the only path around Gatekeeper is a trip
  to System Settings. This is why signing is the prerequisite rather than a
  nicety.

**Replacing and launching other apps**
- macOS 13+ has an **App Management** TCC permission: an app that modifies or
  replaces another app's bundle in `/Applications` or `~/Applications` is
  blocked unless the user grants it — *except* when both are signed by the
  same Team ID. Because the installer and all ten widgets share one Team ID,
  installs and updates need no extra permission. Keep it that way: never
  let the installer touch bundles it did not sign.
- `~/Applications` needs no admin rights; `/Applications` needs an
  authorization prompt. The plan defaults to the former.
- **SMAppService** (Start at Login) only registers apps that live in
  `/Applications` or `~/Applications` (or inside another app's bundle), and
  the first registration on a Mac shows a system notification "Background
  Items Added" naming the developer. That name is whatever the Developer ID
  certificate says, so it will read "Nick Smith" — worth knowing so it is
  not mistaken for a problem.
- The installer cannot register Start at Login *for* another app; each app
  has to do it itself, hence the `--start-at-login` launch argument in the
  plan.

**Permissions the widgets need (TCC)**
- Accessibility: KeyLight (CGEventTap), Barn (Visible Icons only),
  MacRecorder (hotkey tap), Apollo Monitor (volume-key tap). The system
  prompt appears on first use; the installer's permissions screen can only
  deep-link to the pane, never grant.
- Screen Recording: MacRecorder. On macOS 15+ the system **re-asks every
  month** (and after every reboot at first) for apps that capture the
  screen — a Sequoia behaviour, not a bug in the app. Document it on the
  page so it does not read as breakage.
- No usage-description strings are needed for those two, but any app that
  sends Apple Events (VPN & DNS opens the Tailscale app) needs
  `NSAppleEventsUsageDescription` in Info.plist or the call fails silently
  under the hardened runtime. Audit Info.plist keys per app in phase 2.
- Privacy manifests (`PrivacyInfo.xcprivacy`) are an App Store requirement
  and not needed for Developer ID.

**The installer itself**
- It is a downloaded, signed, notarized app too, so everything above applies
  to it, plus self-update: replacing its own bundle while running means
  download → verify → swap on next launch (or relaunch via a tiny signed
  helper), not an in-place overwrite.
- Do not bundle the widget zips inside the installer to skip the download
  step; that makes the installer the thing that has to be re-notarized for
  every widget release. The manifest keeps them independent.

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
  (or `_ScreenCapture`). Barn's Accessibility need is optional (Manage
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

1. **Admin (Nick):** join the Developer Program, accept the Program License
   Agreement, create the Developer ID certificate, store notary credentials,
   record the Team ID. Nothing else starts before this.
2. **Signed builds:** `release-app.sh`, hardened-runtime audit, tag and
   notarize one app (KeyLight) end to end by hand. Confirm a fresh Mac opens
   it with no Gatekeeper warning.
3. **CI:** the reusable GitHub Actions workflow; tag all ten apps and
   StatusItemKit; publish the manifest; wire `--start-at-login` and
   `--unregister-login` into StatusItemKit's `LoginItem`.
4. **Installer app:** checklist → install → permissions, against the real
   manifest. Test on a clean user account and on a Mac with no Xcode.
5. **Manage/updates/removal**, DMG, self-update, site buttons, rewrite of the
   Install sections. Human end-to-end read of the installer's network and
   file code (see "AI-assisted development and Apple review"). Announce.

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
