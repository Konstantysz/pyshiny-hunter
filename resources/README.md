# Resources Directory

This directory contains data files used by PyShiny Hunter.

## Directory Structure

```
resources/
├── pokemon_names/     # ✅ LEGAL - Included in repository
│   ├── gen1.csv       # Pokemon names from Gen 1 (Kanto)
│   ├── gen2.csv       # Pokemon names from Gen 2 (Johto)
│   ├── gen3.csv       # Pokemon names from Gen 3 (Hoenn)
│   ├── gen4.csv       # Pokemon names from Gen 4 (Sinnoh)
│   ├── gen5.csv       # Pokemon names from Gen 5 (Unova)
│   ├── gen6.csv       # Pokemon names from Gen 6 (Kalos)
│   ├── gen7.csv       # Pokemon names from Gen 7 (Alola)
│   ├── gen8.csv       # Pokemon names from Gen 8 (Galar)
│   └── gen9.csv       # Pokemon names from Gen 9 (Paldea)
└── black2/            # ❌ Git ignored (may contain copyrighted assets)
```

## Legal Status

### ✅ `pokemon_names/` - LEGAL
These CSV files contain **factual information only**:
- Pokemon names (not copyrightable)
- Pokedex numbers (factual data)

**Source**: Compiled from publicly available databases (PokeAPI, Bulbapedia)
**Legal Basis**: Facts are not copyrightable under US Copyright Law
**Status**: ✅ Included in Git repository

### ❌ `black2/` - Git Ignored
This directory may contain game-specific assets extracted from ROMs:
- Sprite images (copyrighted by Nintendo)
- Audio files (copyrighted)
- Other game data (copyrighted)

**Status**: ❌ Git ignored (see `.gitignore`)
**Legal**: Do not commit copyrighted Nintendo assets

## CSV File Format

Each CSV file has the format:
```csv
number,name
1,Bulbasaur
2,Ivysaur
3,Venusaur
...
```

### Fields
- `number`: National Pokedex number (integer)
- `name`: Pokemon name in English (string)

### Usage in Code
```python
# Load Pokemon database
with open("resources/pokemon_names/gen1.csv", "r") as f:
    for line in f:
        number, name = line.strip().split(",")
        pokemon_db[name] = int(number)
```

## Adding New Generations

To add support for new Pokemon generations:

1. Create `genX.csv` with the same format
2. Add to the list in `black2_hunter.py`:
   ```python
   for gen_file in ["gen1.csv", ..., "genX.csv"]:
   ```
3. Ensure data is from public sources (not extracted from ROMs)

## Data Sources (Legal)

These files are compiled from publicly available sources:
- [PokeAPI](https://pokeapi.co/) - Open Pokemon API
- [Bulbapedia](https://bulbapedia.bulbagarden.net/) - Pokemon encyclopedia
- [Serebii](https://www.serebii.net/) - Pokemon database

**Note**: We only use factual information (names, numbers), not copyrighted content (images, descriptions).

## Copyright Notice

Pokemon® is a registered trademark of Nintendo, Game Freak, and Creatures Inc.
This project is not affiliated with Nintendo.

The Pokemon name data in this directory:
- ✅ Is factual information (not copyrightable)
- ✅ Can be legally distributed
- ✅ Does not infringe Nintendo's copyrights

See [LEGAL.md](../LEGAL.md) for full copyright policy.