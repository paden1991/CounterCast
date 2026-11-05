# CounterCast spell selection

Version 1.0.0-rc8. WoW Forever, interface 16001.

The existing options window has a **Choose spells** button. `/countercast spells` opens the picker directly; `/countercast list` retains the diagnostic list. A checkbox selects each current-class spell family, with its icon, type and availability. All current choices remain enabled by default.

Preferences save account-wide under `CounterCastDB.disabledSpells`, keyed by the family's lowest rank ID. The client still confirms a learned rank and appropriate pet. Unknown spell IDs cannot be enabled through the setting function. Racial controls are labelled when unavailable. Selecting none removes active buttons outside combat and never deletes saved macros.

Protected actions remain unchanged in combat. Selection changes set the existing dirty/pending flags and rebuild after combat ends. The working macro ownership/reuse logic is unchanged. Appearance reset does not reset spell choices. The two menus reuse their frames.

Validation: 147/147 Lua 5.1 checks, including 26 new selection checks across all nine classes. Covers persistence, ranks, pet/racial abilities, all/none, legacy controls, independent class preferences, invalid saved data, callbacks and combat deferral. Existing macro-reuse and cooldown tests still pass. Live-game acceptance remains separate from offline/simulator testing.

UIForever validation (2026-11-05): Forever build 1.60.1.70450, 1920x1080, UI scale 0.71, Tauren Druid. Clicked the War Stomp checkbox and observed the learned selection count drop from two to one. Select none displayed the no-buttons message; select all restored both learned abilities. After deselecting War Stomp and reloading, saved preferences and the single armed ability were asserted in the Lua console. Clicked Choose spells in the appearance window to reopen the picker. Labels, availability text and controls were visually checked; see `spell-selection-preview.png`.

One diagnostic assertion was sent before the simulator reload finished and failed in `console:1`; the same check passed after loading completed. It was not an addon error. After clearing that diagnostic and exercising the menus again, no Lua errors or missing API entries were present. Original simulator addon enablement and resolution were restored. This verifies the settings UI and simulated behavior, not live casting.
