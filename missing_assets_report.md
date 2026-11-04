# Missing Assets Report — CiB dev7

Generated from `_cib_dev7_dump.txt` (2026-11-04).
This lists UI assets that are missing, broken, or placeholder in the current build.

---

## 1. UNIT CARD ICONS

### Pictish units — ALL missing (20 units)
No dedicated `ui/units/icons/` files for any Pictish unit.
Currently use vanilla Viking placeholder cards.

| Unit key | Type |
|----------|------|
| Pictish_Scout_Riders | cavalry |
| Pictish_Tribal_Horsemen | cavalry |
| Pictish_Chosen_Horsemen | cavalry |
| Pictish_Noble_Guard | cavalry (commander) |
| Pictish_Hunters | skirmisher |
| Pictish_Javelinmen | skirmisher |
| Pictish_Chosen_Skirmishers | skirmisher |
| Pictish_Tribal_Archers | archer |
| Pictish_Slingers | archer |
| Pictish_Youth_Spearmen | infantry |
| Pictish_Tribal_Spearmen | infantry |
| Pictish_Hill_Spearmen | infantry |
| Pictish_Tribal_Axemen | infantry |
| Pictish_Raiders | infantry |
| Pictish_Clan_Warriors | infantry |
| Pictish_Sword_Warriors | infantry |
| Pictish_Hill_Raiders | infantry |
| Pictish_Veteran_Spearmen | infantry |
| Pictish_Chosen_Warriors | infantry |
| Pictish_Champion_Warriors | infantry |

### Hiberni units — no dedicated icons
All Hiberni units (Gangani, Concani, Llyn, Trer) currently use generic Britanni `bri_` placeholder icons.
No `hib_` prefix icon folder exists.

---

## 2. FACTION FLAGS — missing `mon_banner`

The following lowercase flag folders are missing `mon_banner.dds` and `mon_banner.png`
(needed for campaign map banners on army stacks):

| Folder | Also missing .dds? |
|--------|--------------------|
| `ui/flags/ambiani/` | Yes — only .png files |
| `ui/flags/brigantes/` | No — has .dds |
| `ui/flags/caledoni/` | No — has .dds |
| `ui/flags/catuvellauni/` | Yes — only .png files |
| `ui/flags/cornavii/` | Yes — only .png files |
| `ui/flags/cornovii/` | Yes — only .png files |
| `ui/flags/damnonii/` | Yes — only .png files |
| `ui/flags/iceni/` | No — has .dds |
| `ui/flags/rome/` | No — has .dds |
| `ui/flags/smertae/` | Yes — only .png files |
| `ui/flags/taexali/` | Yes — only .png files |
| `ui/flags/trinovantes/` | Yes — only .png files |
| `ui/flags/vacomagi/` | Yes — only .png files |
| `ui/flags/venicones/` | Yes — only .png files |
| `ui/flags/votadini/` | Yes — only .png files |

> Note: the PascalCase folders (`England_Brigantes/`, `Caledonia_Caledonii/`, etc.)
> all have full sets. Only the lowercase folders are incomplete.

---

## 3. FACTION TRAIT ICONS — broken or missing

| File | Status |
|------|--------|
| `ui/campaign ui/effect_bundles/trait_catuvellauni` | **Broken** — missing `.png` extension; file will not load in-game |
| `trait_ordovices.png` | Missing — not in pack |
| `trait_parisi.png` | Missing — not in pack |
| `trait_lugi.png` | Missing — not in pack |
| `trait_atrebates.png` | Missing — not in pack |

---

## 4. FRONTEND FACTION SELECTION MAPS — missing

Only 8 factions have a frontend map (`ui/frontend ui/maps/`).
All others use a blank/generic background on the faction selection screen.

**Has map:** Rome, Atrebates, Ambiani, Brigantes, Catuvellauni, Cornovii, Ordovices (file: `ordivices` — typo in filename), Parisi

**Missing map — playable Britanni:**
- Iceni
- Durotriges
- Cantiaci
- Regni (if still playable)
- Silures (if still playable)
- Trinovantes (if still playable)
- Votadini (if still playable)

**Missing map — Hiberni (all):**
- Darini, Gangani, Nagnate (and all other playable Hiberni)

**Missing map — Picti (all):**
- Caledoni, Caereni, Carnonacae, Damnonii, Decantae, Lugi, Novantae, Smertae, Taexali

---

## 5. BUILDING ICONS — placeholder

Many Pictish-culture buildings use `cib_missing` as their icon key, which is a placeholder.
All Pictish administration buildings (`cib_administration_picti_1` through `_4`) and culture
buildings (`cib_culture_feasting_2` through `_4`, `cib_alehouse_4`) are affected.
They appear as a generic "missing" icon in the building browser.

The slot template icon for Pictish buildings is `rom_PLACEHOLDER` — will show wrong (Roman) art.

---

## 6. MINOR ISSUES

- `ui/flags/England_Catuvellani/` and `ui/flags/England_Catuvellani/` both exist (duplicate with
  different capitalization: `Catuvellani` vs `Catuvellani`). Verify which is used in `faction_banners`.
- `ui/frontend ui/maps/map_cib_fact_ordivices.png` — filename typo (should be `ordovices`).
  May cause the faction map to not load if the DB references `ordovices`.
