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

---

## 7. BUILDING CHAIN ICONS — missing

The following building chains have no dedicated icon in `ui/buildings/icons/`
(these icons are used by the in-game building browser and are referenced on buildings.html).

**HAS icon:**

| Chain key | Icon file |
|---|---|
| cib_land_use | cib_land_use.png + cib_land_use_large.png |
| cib_high_value_crops | cib_high_value_crops.png + cib_high_value_crops_large.png |
| cib_hunters_camp | cib_hunters_camp.png + cib_hunters_camp_large.png |
| cib_mead_production | cib_mead_production.png + cib_mead_production_large.png |
| cib_divi_belli | cib_divi_belli.png + cib_divi_belli_large.png |
| cib_divi_iulii | cib_divi_iulii.png + cib_divi_iulii_large.png |

**MISSING icon** (use `cib_missing` placeholder in-game, colored placeholder box on website):

| Chain key | Category | Culture |
|---|---|---|
| cib_wild_gathering | food | All |
| cib_druid | religion | Britanni & Hiberni |
| cib_college_druids | religion | Britanni & Hiberni |
| cib_fountains_gods | religion | All (Celtic) |
| cib_warrior_ancestors | religion | All (Celtic) |
| cib_matrona_cults | religion | Belgi |
| cib_spirits_war | religion | Belgi & Britanni |
| cib_earth_sky | religion | Picti & Belgi |
| cib_goddess_animals | religion | Belgi & Britanni |
| cib_cailleach | religion | Picti |
| cib_sacred_stones | religion | Picti |
| cib_sovereignty | religion | Hiberni & Picti |
| cib_tuatha_danann | religion | Hiberni |
| cib_fir_bolg | religion | Hiberni |
| cib_cult_mil | religion | Hiberni |
| cib_mercatus | market | Romans |
| cib_commercium | market | Romans |
| cib_mercati_fiere | market | Non-Romans |
| cib_comm_terrestre | market | Non-Romans |
| cib_ludes_cultura | entertainment | Romans |
| cib_voluptates | entertainment | Romans |
| cib_cultura_intrat | entertainment | Non-Romans |
| cib_alehouse | entertainment | Non-Romans |
| cib_administration_romani | administration | Romans |
| cib_administration_britanni | administration | Britanni |
| cib_administration_hiberni | administration | Hiberni |
| cib_administration_picti | administration | Picti |
| cib_administration_belgae | administration | Belgi |
| cib_administration_gauls | administration | Galli |
| cib_civ_romani | military | Romans |
| cib_mil_romani | military | Romans |
| cib_mil_gauls | military | Non-Romans |
| cib_barracks | military | All |
| cib_practice_field | military | All |
| cib_workshop | military | All |
| cib_harbour | port | All |
| cib_tin | production | All |
| cib_bronze | production | All |
| cib_lead | production | All |
| cib_copper | production | All |
| cib_iron | production | All |
| cib_silver | production | All |
| cib_gold | production | All |
| cib_wood | production | All |
| cib_salt | production | All |
| cib_wine | production | All |
| cib_amber | production | All |
| cib_glass | production | All |
| cib_tannery | production | All |
| cib_cloth | production | All |
| cib_pottery | production | All |
| cib_forge | production | All |
| cib_mint | production | All |

> On buildings.html, missing icons display a colored placeholder box with a category symbol.
> When you add an icon, place it at `images/buildings/[chain_key].png` relative to the site root
> and the `<img>` tag in buildings.html will pick it up automatically.
