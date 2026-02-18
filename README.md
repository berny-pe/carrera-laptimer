# carrera-laptimer

Lightweight analog lap timer for slotcar racing on Raspberry Pi.
The app reads lane signals via GPIO and exposes a small Flask web UI.

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

- `GET /`: main page
- `GET /elapsed`: total time HTML fragment
- `GET /lap_times`: lap section HTML fragment

### api routes (json)

- `POST /api/start_timer`
- `POST /api/continue_timer`
- `POST /api/stop_timer`
- `POST /api/reset`
- `POST /api/lap1`
- `POST /api/lap2`
- `GET /api/check_finished`

## run

```bash
python CarreraLapTimer.py
```

## tests

Unit tests focus on the timing core in `lap_timer/core.py`.

```bash
python -m unittest discover -s tests -v
```
