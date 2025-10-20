# Unified Multi-Process GUI

## Overview

PyShiny Hunter now supports **unified multi-process mode** with a single GUI window displaying multiple emulator streams in real-time.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│          MAIN PROCESS - Unified GUI                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Worker 0 │  │ Worker 1 │  │ Worker N │  (Panels)   │
│  │ Display  │  │ Display  │  │ Display  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│       ↑              ↑              ↑                   │
└───────┼──────────────┼──────────────┼───────────────────┘
        │              │              │
    Queue(screenshots @ 60 FPS + stats)
        │              │              │
┌───────┼──────────────┼──────────────┼───────────────────┐
│  WORKER PROCESS 0    │  WORKER 1    │  WORKER N         │
│  ┌──────────────┐    │              │                   │
│  │ DeSmuME      │ (Headless - no GUI)                   │
│  │ Black2Hunter │                                        │
│  └──────────────┘                                        │
│  → Queue.put(screenshot, stats, state)                  │
└─────────────────────────────────────────────────────────┘
```

## Usage

### Single Mode (Default)

Run a single emulator with integrated GUI:

```bash
python scripts/py_desmume_hunter.py roms/black2.nds --state roms/states/black2/ready.dst
```

### Multi-Process Mode

Run multiple emulators with unified GUI:

```bash
# 2 workers
python scripts/py_desmume_hunter.py roms/black2.nds --state roms/states/black2/ready.dst --num-workers 2

# 4 workers
python scripts/py_desmume_hunter.py roms/black2.nds --state roms/states/black2/ready.dst --num-workers 4

# 4 workers with randomized starts
python scripts/py_desmume_hunter.py roms/black2.nds --state roms/states/black2/ready.dst --num-workers 4 --randomize-start
```

## Features

### Real-Time Video Streaming

- Each worker streams screenshots @ 60 FPS
- Main GUI displays all streams side-by-side
- Live updates with minimal latency

### Per-Worker Stats

Each worker panel shows:

- Live emulator video feed (256×384)
- Current state (Search / Check Shiny / Battle)
- Frame counter
- Total encounters
- Encounter breakdown by Pokemon
- Status indicator (Running / Stalled)

### Aggregate Statistics

Unified stats panel displays:

- Total encounters across all workers
- Number of active workers
- Shiny probability calculations
- GUI FPS

### Automatic Shiny Detection

- Each worker independently hunts for shinies
- Automatic save state creation when shiny found
- Save files named: `shiny_worker{N}_{frame_diff}.dst`

## Technical Details

### Headless Mode

Workers run in headless mode (no GUI overhead):

- `PyDeSmuMEManager(headless=True)` - skips GLFW/ImGui initialization
- Emulator logic runs at full speed
- Screenshots captured and sent to main process

### Inter-Process Communication

- **Screenshot Queue**: Workers → Main GUI
  - Contains: screenshot, state, encounters, frame number
  - Max size: `num_workers × 10` frames
  - Non-blocking puts (drops frames if full)
- **Control Queues**: Main GUI → Workers
  - Reserved for future features (pause/resume, commands)

### Performance

- Each worker runs in separate Python process
- No py-desmume multi-instance limitations (1 DeSmuME per process)
- Scales linearly with CPU cores
- GUI maintains 60 FPS even with 4+ workers

## GUI Layout

### 2 Workers

```
┌─────────────────────────────────────────────┐
│     PyShiny Hunter - Multi Mode             │
├──────────────┬──────────────┬───────────────┤
│  Worker 0    │  Worker 1    │ Aggregate     │
│ ┌──────────┐ │ ┌──────────┐ │  Stats        │
│ │          │ │ │          │ │               │
│ │  VIDEO   │ │ │  VIDEO   │ │ Total: 15    │
│ │          │ │ │          │ │ Workers: 2    │
│ └──────────┘ │ └──────────┘ │ Shiny: 0.12% │
│ State: Search│ State: Battle│ FPS: 60      │
│ Frame: 1234  │ Frame: 5678  │               │
│ Encounters:3 │ Encounters:7 │               │
└──────────────┴──────────────┴───────────────┘
```

### 4 Workers

```
┌───────────────────────────────────────────────────────────┐
│            PyShiny Hunter - Multi Mode                    │
├─────────┬─────────┬─────────┬─────────┬───────────────────┤
│ Worker0 │ Worker1 │ Worker2 │ Worker3 │ Aggregate Stats   │
│ [VIDEO] │ [VIDEO] │ [VIDEO] │ [VIDEO] │                   │
│ ...     │ ...     │ ...     │ ...     │ Total: 42         │
└─────────┴─────────┴─────────┴─────────┴───────────────────┘
```

## Troubleshooting

### Workers Not Starting

- Check ROM path is valid
- Verify save state exists (if using `--state`)
- Ensure sufficient CPU resources

### GUI Freezing

- Reduce number of workers
- Check for CPU bottleneck
- Monitor process CPU usage

### Stalled Workers

- Red "Status: STALLED" indicates no updates for 2+ seconds
- Check worker process logs for errors
- May indicate crash or deadlock

### Performance Issues

- **High CPU**: Expected with multiple emulators
- **Low FPS**: Reduce worker count or close other applications
- **Memory**: Each worker uses ~200-300 MB

## Known Limitations

1. **py-desmume**: Only 1 DeSmuME instance per process (design limitation)
2. **Screenshot bandwidth**: ~60 MB/s per worker (256×384×4 bytes @ 60 FPS)
3. **Queue buffering**: Limited to 10 frames per worker to avoid memory buildup

## Future Enhancements

- [ ] Pause/resume individual workers via GUI
- [ ] Save state rotation across workers
- [ ] Centralized shiny detection logging
- [ ] Performance metrics dashboard
- [ ] Worker CPU/memory monitoring
- [ ] Configurable screenshot compression

## Implementation Files

- `scripts/py_desmume_hunter.py` - Main launcher with multi-mode support
- `pyshiny_hunter/py_desmume_manager.py` - Added `headless=True` parameter
- `docs/UNIFIED_GUI.md` - This documentation

## Credits

Implemented as part of Phase 5: Multi-Processing Architecture (2025-10-21)
