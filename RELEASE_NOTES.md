CounterCast 1.0.0-rc8 adds a spell-selection menu for WoW Forever / Interface 16001.

- Open `/countercast spells` or click **Choose spells** in the options menu.
- Select individual abilities, all, or none. Preferences follow all ranks of each spell and save account-wide.
- Changes made during combat apply after combat ends; existing appearance settings and defaults remain unchanged.
- Includes rc7's macro-reuse repair for matching saved macros, including full character macro lists. No existing macros are deleted.

Validation: 147/147 Lua 5.1 checks; UIForever checkbox, all/none, menu navigation and reload-persistence checks. Published runtime is byte-identical to the reviewed installed rc8 update. Simulator checks do not certify live-game casting.

In WowUp, select Forever and use Install from URL with https://github.com/paden1991/CounterCast (without `.git`). Use the Beta channel for this release candidate. Download the attached `CounterCast-1.0.0-rc8-forever.zip`, not GitHub's source archive. Extract its CounterCast folder into Interface/AddOns and reload outside combat.

The release includes Forever metadata and SHA-256 checksum. See the repository README for the menu preview and detailed verification.
