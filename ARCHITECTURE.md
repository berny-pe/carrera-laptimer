# Architecture

Architecture and design decisions of the Slotcar Laptimer (v1.1.1).

## Overview

Lightweight Flask web app that times slot car races on a Raspberry Pi. Photoelectric sensors on each lane feed GPIO pins; the browser (tablet, laptop) shows live lap data. Any number of lanes is supported (one GPIO pin per lane), and a race is either a **lap race** (first to N laps) or a **time race** (most laps within a time limit).

## Project Structure

```
slotcar-laptimer/
├── SlotcarLapTimer.py       # Flask entry point and routes
├── VERSION                  # Project version
├── requirements.txt         # flask, rpi-lgpio (Pi only)
├── README.md                # Quick start
├── ARCHITECTURE.md          # This file
├── BUILDERS_GUIDE.md        # Hardware assembly and setup
├── CONTRIBUTING.md          # Contribution guide
├── lap_timer/
│   ├── config.py            # LANE_PINS, MIN_LAP_SECONDS
│   ├── lanes.py             # Resolves lane pins (SLOT_LANE_PINS env override)
│   ├── core.py              # LapTimer + LaneState: timing, race modes, winner logic
│   └── gpio_adapter.py      # GPIOLapSensor: pin setup and edge callbacks
├── templates/
│   ├── setup.html           # Race setup screen (mode, laps/time, lanes)
│   ├── index.html           # Race screen layout
│   ├── elapsed.html         # Total time / goal / status fragment
│   └── lap_times.html       # Per-lane lap data fragment
├── static/
│   ├── css/index.css        # Styling (setup + race screens)
│   └── js/
│       ├── setup.js         # Setup form -> POST /api/configure
│       └── index.js         # Race controls and polling
├── tests/
│   ├── test_core.py         # Timing core tests (35)
│   └── test_app.py          # Flask route tests (12)
└── .github/                 # CI workflow (unit tests) and dependabot
```

## Modules

### SlotcarLapTimer.py (entry point)

Creates the Flask app, one shared `LapTimer`, and one `GPIOLapSensor` wired to it. Route handlers are thin and delegate to `LapTimer`.

| Route | Purpose |
|-------|---------|
| `GET /` | Setup screen; redirects to `/race` if a race is configured |
| `GET /race` | Race screen; redirects to `/` if not configured |
| `GET /elapsed` | HTML fragment: total time, goal, status |
| `GET /lap_times` | HTML fragment: per-lane lap data |
| `POST /api/configure` | `{"mode":"laps","laps":10}` or `{"mode":"time","time_seconds":300}`, optional `"lanes":[1,3]`. 400 on invalid input |
| `POST /api/start_timer` | Start; 409 until configured |
| `POST /api/continue_timer` | Resume after stop |
| `POST /api/stop_timer` | Pause |
| `POST /api/reset` | Clear everything, back to setup |
| `POST /api/lap/<lane>` | Manual lap trigger (1-based); 404 for unknown lane. `/api/lap1`, `/api/lap2` are legacy aliases |
| `GET /api/check_finished` | `{"finished": bool}` |

The app runs with `use_reloader=False`: the reloader imports the module twice and the second process fails with "Failed to add edge detection" because the pins are already claimed.

### lap_timer/config.py and lanes.py

`LANE_PINS` is a list of BCM pins, one per lane, in lane order. Its length is the lane count (2-lane default, commented 4-lane example). `lanes.lane_pins()` returns `config.LANE_PINS`, unless the `SLOT_LANE_PINS` env var (`"18,23,24,25"`) overrides it. Duplicate or non-numeric pins raise `ValueError`.

`MIN_LAP_SECONDS = 1.0` is the debounce window: a second crossing on the same lane within it is ignored.

### lap_timer/core.py

**`LaneState`** (dataclass): `finished`, `last_total_time`, `lap_time` (current lap in progress), `last_lap_time`, `fastest_lap_time`, `num_laps`, `active` (inactive lanes ignore laps and are hidden).

**`LapTimer`**: all state behind one `threading.Lock`. Lane count comes from `lane_pins()` unless passed explicitly.

- Lifecycle: `configure()`, `start_timer()`, `stop_timer()`, `continue_timer()`, `reset()`
- Lap input: `lap_callback(lane_number, channel=None)` (GPIO and manual use the same path); `lap()` and `lap_callback1/2` are wrappers
- Queries: `check_finished()`, `time()`, `get_template_data()`, `get_formatted_time()` (`MM:SS:mmm`)
- Internals: `_register_lap`, `_expire_if_needed`, `_winner`, `_race_info`

**Race modes** (set via `configure()`, only before the race starts):

- `laps`: target 1-999. A lane finishes when it reaches the target. The race ends when every active lane finished.
- `time`: limit 1 s - 4 h. When the limit is reached the clock stops (`ended = True`) and each lane finishes on its next line crossing; that lap still counts.

**Winner**: most laps; ties go to the lane that crossed the line first. A true tie (same laps and timestamp) yields `0`. Undecided until all active lanes finished.

**Lap registration** (`_register_lap`):
1. Ignore if lane finished, inactive, or the race never started.
2. Expire a time race if the limit passed.
3. Ignore if closer than `MIN_LAP_SECONDS` to the previous crossing (bounce).
4. Compute lap time (since previous crossing, or since start), update fastest, count the lap.
5. Mark the lane finished if the lap target is reached or the timer is no longer running.
6. If the timer is running and all active lanes are finished, end the race.

**Pause accounting**: elapsed = `now - start_time - paused`. `stop_timer` records `last_active_time`; `continue_timer` adds the pause length to `paused`. A race that has `ended` cannot be restarted or continued; use reset.

### lap_timer/gpio_adapter.py

`GPIOLapSensor(pins=None)` registers `GPIO.BOTH` edge detection per pin with `partial(lap_timer.lap_callback, lane_number)`. If the GPIO library is missing (laptop, CI), `setup()` returns `False` and the app runs without sensors; manual lap buttons still work. The Pi dependency is `rpi-lgpio`, a drop-in `RPi.GPIO` replacement that works on current Raspberry Pi OS.

## Frontend

- **setup.html / setup.js**: choose mode, laps or minutes, and lanes (checkboxes shown when more than one lane exists). Submits to `/api/configure`, then navigates to `/race`.
- **index.html / index.js**: race screen. Start runs a five-light CSS countdown with a random delay, then calls `/api/start_timer` and starts polling. Buttons: Start, Continue, Stop, one Lap button per active lane, Refresh, Reset (confirms, then returns to setup).
- **Polling** (`setInterval`): elapsed 345 ms, lap times 654 ms, finished check 125 ms. All intervals stop once `check_finished` returns true.
- **Fragments**: `/elapsed` and `/lap_times` return server-rendered HTML that replaces `#elapsed` and `#lap_times`.
- **CSS**: lane colors `.lane-1` to `.lane-6` (blue, red, green, orange, purple, teal), large fonts for tablets.

## Data Flow

```
Setup screen --POST /api/configure--> LapTimer.configure()  -> redirect /race
Start button --lights--> POST /api/start_timer -> LapTimer.start_timer()
Car crosses sensor -> GPIO edge -> GPIOLapSensor callback
        -> LapTimer.lap_callback(lane) -> _register_lap()
Browser polls /elapsed, /lap_times -> get_template_data() -> HTML fragments
All active lanes finished -> check_finished() true -> polling stops, winner shown
Reset -> POST /api/reset -> LapTimer.reset() -> setup screen
```

## State

```
[UNCONFIGURED] --configure--> [CONFIGURED] --start--> [RUNNING]
[RUNNING] --stop--> [PAUSED] --continue--> [RUNNING]
[RUNNING] --lap target reached by all / time limit--> [ENDED]
(PAUSED: a lap crossing marks that lane finished)
any state --reset--> [UNCONFIGURED]
```

Time race: after the limit the status reads "Time is up - finish your lap" until all active lanes cross the line once more.

## Testing

```bash
python -m unittest discover -s tests -v
```

- `tests/test_core.py` (35 tests): `LapTimerCoreTests` (timer, laps, formatting, pause), `RaceModeTests` (lap and time modes, validation, winner), `MultiLaneTests` (N lanes, lane selection, bounce).
- `tests/test_app.py` (12 tests): `AppRouteTests` (routes, redirects, error codes). Needs Flask installed.
- CI (`.github/workflows/python-tests.yml`) runs the suite on every push and PR with Python 3.13.

Core tests patch `lap_timer.core.time.time` for deterministic timing.

## Design Decisions

1. **One lock, thread-safe core.** GPIO callbacks run on their own thread while Flask serves requests. A single `Lock` is simple and sufficient.
2. **Core free of hardware and web code.** `core.py` imports neither Flask nor GPIO, so it is unit-testable anywhere.
3. **GPIO adapter with graceful fallback.** No GPIO library means no sensors, not a crash.
4. **Pin list instead of fixed lanes.** Lane count is data (`LANE_PINS`), not code; the env override avoids editing files per track.
5. **Server-side formatting.** Times are formatted once in Python; the browser only inserts HTML.
6. **Polling over WebSockets.** Simple, works in any browser, fine for a few clients on a LAN.
7. **Client-side start lights.** Countdown is pure CSS/JS, independent of network latency.
8. **Debounce in core.** `MIN_LAP_SECONDS` filters double triggers regardless of sensor hardware.

## Limitations and Security

- Single race state shared by all clients; no history is stored.
- No authentication, HTTPS or rate limiting. The server binds `0.0.0.0` and `/api/reset` is open to anyone on the network. Use a trusted LAN or a dedicated hotspot.
- `debug=True` is set in `app.run` (reloader off). Debug mode exposes the Werkzeug console, so avoid running on untrusted networks.
- Timing accuracy is bounded by sensor response, GPIO edge latency and the OS scheduler; expect millisecond-level resolution, not guaranteed precision.

## Build and Deployment

See [README.md](README.md) for install and run, and [BUILDERS_GUIDE.md](BUILDERS_GUIDE.md) for hardware.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests
python SlotcarLapTimer.py        # http://<pi-ip>:5000
```
