# Sonic USB Online 1.47.19 — extension support roadmap

This roadmap is based on the attached `SonicUSBOnline_1.47.19.ccn` structural/object inventory. It is not a claim that the game currently exports or runs.

## Goal

Preserve the game's extension objects and implement their actual event behavior in NuclearRT. Do not strip extension objects or replace them with successful-looking no-op stubs. Unknown actions/conditions/expressions should be logged as unsupported so the export can be diagnosed.

## Priority order

1. **Text Blitter (`TLBT`, 831 object definitions)** — needed throughout menus and UI. First inspect the actions, conditions and expressions referenced by the first startup/menu frames, then implement the subset used there. Rendering must match the game's bitmap-font/text behavior sufficiently for layout and transparency.
2. **KcArray (`0RRA`, 23 object definitions)** — implement and test all array reads/writes, dimensions, indexing, clear/load/save operations used by the game. Save paths and string-vs-number behavior must be checked.
3. **Lacewing (`OCli`, 3 object definitions)** — preserve object/event metadata and identify required Relay Client operations. A functional online port requires protocol-compatible networking; dummy handlers are not equivalent.
4. **Other used extensions** — inspect actual event references before prioritizing Parallaxer (`xlap`), Box2D-related objects (`GE2B`, `úï2B`), Mode 7 (`1X7M`), Value-Add (`AVAD`), String Parser (`PSE3`), layer/perspective, file, input, and other extension families.

## First boot path

The CCN's initial frames include:

- Server status
- Check update
- Data check
- Data Warning
- Username Screen
- Control Check
- Mapping
- Control
- Warnings
- Startup
- Franck lecaille presents
- Selphy Game
- preTitle Screen
- Title Screen
- Options
- Sound Test

Start with the first reachable path and record the frame transition, events, and extension calls at each stage. The fact that an extension has many object definitions does not by itself tell us which actions the first frame executes.

## Implementation rules

- Add an exporter to `ExtensionExporterRegistry` only alongside the matching runtime class and event handlers.
- Preserve extension object identifiers and per-object initialization data.
- For unsupported extension calls, emit a diagnostic with extension ID, action/condition/expression number, and frame name/index. Do not silently treat a missing condition as true or an expression as a meaningful zero.
- Keep offline and online goals distinct: a local menu test can pass while Lacewing-dependent multiplayer remains unimplemented.
- Verify in stages: (1) exporter parses the CCN, (2) generated C++ compiles, (3) startup frame renders, (4) title/options screens work, (5) level loads, (6) online networking works.

## Current status

- The CCN-only **exporter tool** compiles for Windows x64 in [GitHub Actions run 39693471992](https://github.com/sdsdsdsrj4rjj/Thing-to-transfer-via-gitclone-on-rg34xx/actions/runs/39693471992).
- That run does not export or build Sonic USB Online.
- The separate runtime smoke-test executable is an empty fixture and is not the game.
- Extension behavior has not yet been implemented or verified by a playable build.
