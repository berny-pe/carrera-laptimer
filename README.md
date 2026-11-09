# Slotcar Laptimer

Lightweight analog lap timer for slotcar racing simply on a Raspberry Pi and a tablet.
The app reads lane signals via GPIO and exposes a small Flask web UI that can be opened on an iPad or any other tablet for interactive racing.
2 racemodes are supported:
- number of laps to race
- race duration

## refactored architecture

- `SlotcarLapTimer.py`: Flask entrypoint and route wiring
- `lap_timer/core.py`: pure timing and lap domain logic (`LapTimer`, `LaneState`)
- `lap_timer/gpio_adapter.py`: GPIO integration and callback registration
- `lap_timer/config.py`: constants (`LANE_PINS` = one GPIO pin per lane; its length is the lane count)
- `lap_timer/lanes.py`: resolves the lane pins, including the `SLOT_LANE_PINS` env override
- `templates/`: server-rendered HTML fragments and page template
- `static/css/index.css`: extracted page styling
- `static/js/index.js`: extracted frontend interaction logic

## routes

### page + html fragment routes

- `GET /`: race setup screen (redirects to `/race` while a race is configured)
- `GET /race`: race screen (redirects to `/` if no race is configured)
- `GET /elapsed`: total time HTML fragment
- `GET /lap_times`: lap section HTML fragment

### api routes (json)

- `POST /api/configure`: `{"mode": "laps", "laps": 10}` or `{"mode": "time", "time_seconds": 300}`, each optionally with `"lanes": [1, 3]` to pick the participating lanes (default: all); only before the race starts
- `POST /api/start_timer` (409 until configured)
- `POST /api/continue_timer`
- `POST /api/stop_timer`
- `POST /api/reset`
- `POST /api/lap/<lane>` (1-based; `/api/lap1` and `/api/lap2` remain as aliases)
- `GET /api/check_finished`

## race modes

After opening the app (or after a reset) the setup screen asks for either a
number of laps or a race time.

- **Laps:** a lane finishes when it completes the target laps; the race ends
  when all participating lanes are finished. Winner = first to finish.
- **Time:** the clock stops at the limit; each lane finishes on its next
  line crossing (that lap still counts). Winner = most laps, ties go to the
  car that crossed the line first.

Reset returns to the setup screen.

## lanes

The lane count comes from `LANE_PINS` in `lap_timer/config.py` (currently 2 lanes
on BCM pins 18 and 23; a commented-out 4-lane line with pins 24 and 25 is
included - adjust to your wiring). To override it without editing code:

```bash
SLOT_LANE_PINS="18,23,24,25" python SlotcarLapTimer.py   # 4-lane track
```

The setup screen lets you choose which lanes take part, so a 4-lane track can
run a 2-car race. Lanes that are not selected are hidden and ignored.
A race ends when every participating lane has finished.

## install on a Raspberry Pi

Tested on Raspberry Pi OS (Bookworm or newer). From the repo folder:

```bash
sudo apt update
sudo apt install -y swig python3-dev python3-venv liblgpio-dev
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

GPIO uses `rpi-lgpio`, a drop-in `RPi.GPIO` replacement. The old `RPi.GPIO` package
fails with "Failed to add edge detection" on current Raspberry Pi OS. `rpi-lgpio` compiles
a C extension, which is why the apt packages above are needed first (without `swig`
the install fails with "command 'swig' failed"). The build takes a minute or two.

## run

```bash
source .venv/bin/activate
python SlotcarLapTimer.py
```

On a machine without a Pi (e.g. a laptop) the GPIO part is skipped automatically;
`pip install -r requirements.txt` is enough there.

## tests

Unit tests focus on the timing core in `lap_timer/core.py`.

```bash
python -m unittest discover -s tests -v
```
