# Architecture Overview

PyShiny Hunter is designed with a clean, modular architecture following software engineering best practices.

## System Architecture

### High-Level Components

```text
┌─────────────────────────────────────────────────────────────┐
│                     PyShiny Hunter                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   CLI Layer  │  │  GUI Process │  │ Worker Processes│   │
│  │              │  │              │  │                 │   │
│  │ • Argument   │  │ • ImGui      │  │ • Headless      │   │
│  │   Parsing    │  │ • OpenGL     │  │   Emulators     │   │
│  │ • Mode       │  │ • Texture    │  │ • Screenshot    │   │
│  │   Selection  │  │   Rendering  │  │   Streaming     │   │
│  └──────────────┘  └──────────────┘  └─────────────────┘   │
│         │                  │                    │            │
│         └──────────────────┴────────────────────┘            │
│                            │                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Hunter State Machine                      │ │
│  │  ┌────────┐  ┌────────┐  ┌──────┐  ┌────────┐        │ │
│  │  │ Search │→ │  Check │→ │ Pre- │→ │ Battle │        │ │
│  │  │        │  │  Shiny │  │Battle│  │        │        │ │
│  │  └────────┘  └────────┘  └──────┘  └────────┘        │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          Computer Vision Pipeline                      │ │
│  │                                                         │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐│ │
│  │  │Animation │  │  Sparkle │  │   Enhanced OCR       ││ │
│  │  │Detection │  │Detection │  │ ┌─────────────────┐  ││ │
│  │  │          │  │          │  │ │ EasyOCR         │  ││ │
│  │  │• Frame   │  │• Bright  │  │ │ SymSpell        │  ││ │
│  │  │  Count   │  │  Pixel   │  │ │ Fuzzy Matching  │  ││ │
│  │  │• Diff    │  │  Area    │  │ └─────────────────┘  ││ │
│  │  │  Thresh  │  │  Calc    │  │                      ││ │
│  │  └──────────┘  └──────────┘  └──────────────────────┘│ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          DeSmuME Emulator Integration                  │ │
│  │                                                         │ │
│  │  • ROM Loading          • Screen Capture               │ │
│  │  • Save States          • Input Management             │ │
│  │  • Frame Stepping       • FPS Tracking                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Module Organization

### Core Modules

#### `hunter.py` - Abstract Base Class

```python
class Hunter(StateMachine):
    """State machine for hunting workflow."""

    # States
    search = State(initial=True)
    check_shiny = State()
    pre_battle = State()
    battle = State()
    found = State(final=True)

    # Abstract methods (game-specific)
    @abstractmethod
    def check_if_shiny(self, frame: np.ndarray) -> bool:
        pass

    @abstractmethod
    def get_pokemon_name(self, frame: np.ndarray) -> str:
        pass
```

**Responsibilities:**

- Define state machine structure
- Manage state transitions
- Provide extensibility for other games

#### `black2_hunter.py` - Pokémon Black 2 Implementation

```python
class Black2Hunter(Hunter):
    """Black 2 specific implementation."""

    def check_if_shiny(self, frame: np.ndarray) -> bool:
        # Animation frame counting (primary)
        # Sparkle detection (secondary)
        pass

    def get_pokemon_name(self, frame: np.ndarray) -> str:
        # Enhanced OCR pipeline
        pass
```

**Responsibilities:**

- Implement detection algorithms
- Extract screen regions
- Preprocess images for OCR

#### `enhanced_ocr.py` - 3-Stage OCR Pipeline

```python
class EnhancedOCR:
    """3-stage OCR: EasyOCR → SymSpell → Fuzzy Match."""

    def recognize_pokemon_name(self, image: np.ndarray) -> str | None:
        # Stage 1: EasyOCR
        raw_text = self.easyocr_reader.readtext(image)

        # Stage 2: SymSpell spell correction
        corrected = self._apply_symspell_correction(raw_text)

        # Stage 3: Fuzzy matching
        return self._fuzzy_match(corrected, self.pokemon_names)
```

**Responsibilities:**

- Primary OCR with GPU acceleration
- Spell correction using Pokémon dictionary
- Fuzzy matching for error tolerance

### Process Management

#### `py_desmume_manager.py` - Emulator Integration

```python
class PyDeSmuMEManager:
    """Manages DeSmuME emulator lifecycle."""

    def __init__(self, rom_path: str, headless: bool = False):
        if not headless:
            self.__initialize_glfw_window()
            self.__initialize_imgui()
        self.__initialize_emulators()

    def run(self):
        while not glfw.window_should_close(self.window):
            self.__emulators_next_frame()
            self.__process_inputs()
            self.__render_imgui()
```

**Responsibilities:**

- Load ROM and save states
- Capture screenshots (60 FPS)
- Render GUI (single mode)
- Support headless mode (multi-process)

#### `worker_process.py` - Multi-Process Workers

```python
def headless_worker(
    worker_id: int,
    rom_path: str,
    screenshot_queue: mp.Queue,
    shared_stats: dict,
    barrier: mp.Barrier,
    # ...
):
    """Headless emulator worker process."""

    # 1. Load emulator
    manager = PyDeSmuMEManager(rom_path, headless=True)

    # 2. RNG desynchronization
    offset = worker_id * BASE_OFFSET + random.randint(0, JITTER)
    for _ in range(offset):
        manager.emulators[0].emu.cycle()

    # 3. Wait at barrier
    barrier.wait(timeout=30)

    # 4. Stream screenshots
    while True:
        frame = manager.emulators[0].get_screenshot()
        screenshot_queue.put({
            "worker_id": worker_id,
            "frame": frame,
            # ... metadata
        })
```

**Responsibilities:**

- Run headless emulator
- Desynchronize RNG state
- Stream screenshots to GUI
- Update shared statistics

#### `gui_process.py` - Unified GUI

```python
def unified_gui_main_process(
    num_workers: int,
    screenshot_queue: mp.Queue,
    shared_stats: dict,
    # ...
):
    """Main GUI process for multi-worker mode."""

    # Initialize GLFW + ImGui
    window = initialize_window()

    # Main loop
    while not glfw.window_should_close(window):
        # Drain screenshot queue
        while not screenshot_queue.empty():
            data = screenshot_queue.get()
            update_worker_display(data)

        # Render GUI
        render_worker_panels()
        render_aggregate_stats()
        render_shiny_log()
```

**Responsibilities:**

- Receive screenshots from all workers
- Render unified grid layout
- Display aggregate statistics
- Show shiny log panel

### Configuration & Utilities

#### `config.py` - Centralized Configuration

```python
# Shiny detection
SHINY_FRAME_DIFF_THRESHOLD = 500
SHINY_SPARKLE_BRIGHTNESS_THRESHOLD = 247

# OCR
OCR_UPSCALE_FACTOR = 2
OCR_BINARY_THRESHOLD = 128
FUZZY_MATCH_THRESHOLD = 80

# Multi-process
WORKER_RNG_BASE_OFFSET_FRAMES = 60
WORKER_RNG_JITTER_FRAMES = 30
```

**Responsibilities:**

- Define all constants
- Provide tuning parameters
- Document threshold selection

#### `utils/` - Utility Modules

- `gui_utils.py`: OpenGL texture management
- `pokemon_loader.py`: Load Pokémon name databases
- `module_logger.py`: Logging configuration

## Design Patterns

### State Machine Pattern

The `Hunter` class uses `python-statemachine` to manage hunting workflow:

```python
# State transitions
search_to_check_shiny = search.to(check_shiny)
check_shiny_to_pre_battle = check_shiny.to(pre_battle)
pre_battle_to_battle = pre_battle.to(battle)
battle_to_found = battle.to(found, cond="is_shiny")
battle_to_search = battle.to(search, cond="not is_shiny")
```

**Benefits:**

- Clear state flow
- Easy debugging
- Diagram generation

### Strategy Pattern

Computer vision algorithms are encapsulated in methods:

```python
class Black2Hunter(Hunter):
    def _analyze_animation(self, frame: np.ndarray) -> bool:
        """Primary shiny detection: frame counting."""
        pass

    def _calculate_brightness(self, frame: np.ndarray) -> float:
        """Secondary detection: sparkle pixels."""
        pass
```

**Benefits:**

- Swappable algorithms
- Easy A/B testing
- Clear separation

### Multi-Process Architecture

Uses `multiprocessing` module for parallelization:

```text
Main Process
├── GUI (ImGui + OpenGL)
└── Worker Coordination

Worker Process 0
├── DeSmuME Emulator (headless)
├── Black2Hunter (state machine)
└── Screenshot Queue (producer)

Worker Process 1
├── DeSmuME Emulator (headless)
├── Black2Hunter (state machine)
└── Screenshot Queue (producer)

...

Shared Resources (Manager)
├── shared_stats (dict)
├── shared_shiny_log (list)
├── screenshot_queue (Queue)
└── barrier (Barrier)
```

**Benefits:**

- True parallelism (GIL bypass)
- Independent emulator instances
- Centralized statistics

## Data Flow

### Single Mode

```text
ROM File → DeSmuME → Frame → Hunter → GUI
                      ↓
                  Screenshot
                      ↓
              Computer Vision
                      ↓
            ┌─────────┴─────────┐
            ↓                   ↓
    Shiny Detection      OCR Pipeline
            ↓                   ↓
      Is Shiny?          Pokemon Name
            ↓                   ↓
        GUI Update ← Encounters Stats
```

### Multi-Process Mode

```text
Main Process (GUI)
     ↑
     │ screenshot_queue
     │
Worker 0 ─┐
Worker 1 ─┼─→ Screenshots + Metadata
Worker 2 ─┤
Worker 3 ─┘
     │
     └─→ shared_stats (encounters)
     └─→ shared_shiny_log (shinies)
```

## Performance Considerations

### CPU Usage

- **Single Mode**: 100% of 1 core (emulation) + 15-25% GUI
- **Multi-Process (4 workers)**: 400% (4 cores emulation) + 15-25% GUI

### Memory Usage

- **Single Mode**: ~50-100 MB
- **Multi-Process (4 workers)**: ~90-140 MB (efficient queue buffering)

### GPU Usage

- **OCR (with CUDA)**: ~500 MB VRAM
- **OpenGL Textures**: ~10 MB per worker

### Optimization Strategies

1. **Queue Buffering**: Max 10 frames per worker prevents unbounded growth
2. **Non-Blocking Puts**: Drop frames if queue full (maintains 60 FPS)
3. **Lazy OCR**: Only run on encounter (not every frame)
4. **Texture Reuse**: Update existing texture instead of creating new

## Testing Strategy

### Unit Tests

- `test_black2_hunter.py`: Detection algorithms
- `test_enhanced_ocr.py`: OCR pipeline
- `test_config.py`: Configuration loading

### Integration Tests

- `test_py_desmume_manager.py`: Emulator integration
- `test_worker_process.py`: Multi-process coordination

### Data Validation

- `examples/data_exploration_and_algorithm_design.ipynb`
- 1,934 real-world frames analyzed
- 100% OCR accuracy on test dataset

## Extensibility

### Adding New Games

1. **Create subclass:**

   ```python
   class HeartGoldHunter(Hunter):
       def check_if_shiny(self, frame: np.ndarray) -> bool:
           # Game-specific logic
           pass
   ```

2. **Define screen regions:**

   ```python
   HGSS_NAME_REGION = (x1, y1, x2, y2)
   ```

3. **Implement detection:**

   - Animation analysis
   - Sparkle detection
   - Battle detection

4. **Add to CLI:**

   ```python
   parser.add_argument("--game", choices=["black2", "heartgold"])
   ```

### Adding New Features

Framework supports:

- Custom OCR models
- Additional detection algorithms
- New GUI panels
- Discord webhook integration
- Web dashboard

## See Also

- [Usage Guide](usage.rst) - How to use the system
- [API Reference](api/modules.rst) - Detailed module documentation
- [Configuration](configuration.rst) - Tuning parameters
- `docs/UNIFIED_GUI.md` - Multi-process architecture deep dive
