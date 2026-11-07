# carrera-laptimer

Lightweight analog lap timer for slotcar racing on Raspberry Pi.
The app reads lane signals via GPIO and exposes a small Flask web UI that can be opened on an iPad for interactive racing.
2 racemodes are supported:
- number of laps to race
- race duration

## refactored architecture

- `CarreraLapTimer.py`: Flask entrypoint and route wiring
- `lap_timer/core.py`: pure timing and lap domain logic (`LapTimer`, `LaneState`)
- `lap_timer/gpio_adapter.py`: GPIO integration and callback registration
- `lap_timer/config.py`: central pin configuration
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

- `POST /api/configure`: `{"mode": "laps", "laps": 10}` or `{"mode": "time", "time_seconds": 300}`; only before the race starts
- `POST /api/start_timer` (409 until configured)
- `POST /api/continue_timer`
- `POST /api/stop_timer`
- `POST /api/reset`
- `POST /api/lap1`
- `POST /api/lap2`
- `GET /api/check_finished`

## race modes

After opening the app (or after a reset) the setup screen asks for either a
number of laps or a race time.

- **Laps:** a lane finishes when it completes the target laps; the race ends
  when both lanes are finished. Winner = first to finish.
- **Time:** the clock stops at the limit; each lane finishes on its next
  line crossing (that lap still counts). Winner = most laps, ties go to the
  car that crossed the line first.

Reset returns to the setup screen.

## run

```bash
python CarreraLapTimer.py
```

## tests

Unit tests focus on the timing core in `lap_timer/core.py`.

```bash
python -m unittest discover -s tests -v
```
