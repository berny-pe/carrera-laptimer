import time
from dataclasses import dataclass
from threading import Lock

from .config import MIN_LAP_SECONDS
from .lanes import lane_pins


@dataclass
class LaneState:
    finished: bool = False
    last_total_time: float | None = None
    lap_time: float | None = None
    last_lap_time: float | None = None
    fastest_lap_time: float | None = None
    num_laps: int = 0
    # inactive lanes take no part in the race: laps are ignored, not displayed
    active: bool = True


MODE_LAPS = 'laps'
MODE_TIME = 'time'
MAX_LAPS = 999
MAX_TIME_SECONDS = 4 * 3600


class LapTimer:
    def __init__(self, num_lanes=None):
        self.num_lanes = len(lane_pins()) if num_lanes is None else num_lanes
        if not isinstance(self.num_lanes, int) or isinstance(self.num_lanes, bool) or self.num_lanes < 1:
            raise ValueError('num_lanes must be a positive integer')
        self._lock = Lock()
        self.reset()

    @property
    def lane1(self):
        return self.lanes[0]

    @property
    def lane2(self):
        return self.lanes[1]

    def _active_lanes(self):
        return [lane for lane in self.lanes if lane.active]

    def reset(self):
        with self._lock:
            self.timer_running = False
            self.start_time = None
            self.last_active_time = None
            self.paused = 0.0
            self.elapsed_time = None
            self.lanes = [LaneState() for _ in range(self.num_lanes)]
            # race configuration: mode None means a free-running timer
            self.mode = None
            self.target_laps = None
            self.time_limit = None
            # True once the race condition (lap target / time limit) ended the race
            self.ended = False

    @property
    def configured(self):
        return self.mode is not None

    def configure(self, mode, laps=None, time_seconds=None, lanes=None):
        """Select the race condition. Only allowed before the race has started."""
        with self._lock:
            if self.start_time is not None:
                raise ValueError('race already started, reset first')
            active = self._validate_lanes(lanes)
            if mode == MODE_LAPS:
                if not isinstance(laps, int) or isinstance(laps, bool) or not 1 <= laps <= MAX_LAPS:
                    raise ValueError(f'laps must be an integer between 1 and {MAX_LAPS}')
                self.target_laps, self.time_limit = laps, None
            elif mode == MODE_TIME:
                if (not isinstance(time_seconds, (int, float)) or isinstance(time_seconds, bool)
                        or not 1 <= time_seconds <= MAX_TIME_SECONDS):
                    raise ValueError(f'time must be between 1 and {MAX_TIME_SECONDS} seconds')
                self.target_laps, self.time_limit = None, float(time_seconds)
            else:
                raise ValueError("mode must be 'laps' or 'time'")
            self.mode = mode
            for number, lane in enumerate(self.lanes, start=1):
                lane.active = number in active

    def _validate_lanes(self, lanes):
        """Set of participating lane numbers (1-based); None means all lanes."""
        if lanes is None:
            return set(range(1, self.num_lanes + 1))
        if (not isinstance(lanes, (list, tuple, set)) or not lanes
                or any(not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= self.num_lanes
                       for n in lanes)):
            raise ValueError(f'lanes must be a non-empty list of lane numbers between 1 and {self.num_lanes}')
        return set(lanes)

    def _reached_target(self, lane: LaneState):
        return self.mode == MODE_LAPS and lane.num_laps >= self.target_laps

    def _expire_if_needed(self, now):
        """End a time race once the limit is reached. Caller holds the lock."""
        if self.mode != MODE_TIME or not self.timer_running or self.start_time is None:
            return
        if now - self.start_time - self.paused >= self.time_limit:
            self.elapsed_time = self.time_limit
            self.last_active_time = now
            self.timer_running = False
            self.ended = True

    def start_timer(self):
        with self._lock:
            if not self.timer_running and not self.ended:
                self.timer_running = True
                self.start_time = time.time()
                self.last_active_time = None
                self.paused = 0.0
                for lane in self.lanes:
                    lane.finished = self._reached_target(lane)

    def continue_timer(self):
        with self._lock:
            if (not self.timer_running and not self.ended
                    and self.start_time is not None and self.last_active_time is not None):
                self.timer_running = True
                self.paused += time.time() - self.last_active_time
                for lane in self.lanes:
                    lane.finished = self._reached_target(lane)

    def stop_timer(self):
        with self._lock:
            self.last_active_time = time.time()
            if self.timer_running:
                self.elapsed_timer()
                self.timer_running = False

    def elapsed_timer(self):
        if self.timer_running and self.start_time is not None:
            now = time.time()
            self.elapsed_time = now - self.start_time - self.paused
            self._expire_if_needed(now)
        return self.elapsed_time

    def _register_lap(self, lane: LaneState):
        if lane.finished or not lane.active:
            return

        if self.start_time is None:
            return

        now = time.time()
        # a crossing after the time limit still counts: the car finishes its lap
        self._expire_if_needed(now)

        # ignore sensor bounce / double triggers right after a counted lap
        if lane.last_total_time is not None and now - lane.last_total_time < MIN_LAP_SECONDS:
            return

        if lane.last_total_time is not None:
            lane.last_lap_time = now - lane.last_total_time
        else:
            lane.last_lap_time = now - self.start_time

        if lane.fastest_lap_time is None or lane.last_lap_time < lane.fastest_lap_time:
            lane.fastest_lap_time = lane.last_lap_time

        lane.num_laps += 1
        lane.last_total_time = now

        if not self.timer_running or self._reached_target(lane):
            lane.finished = True

        # all lanes reached the lap target while racing: the race is over.
        # (After a manual stop or a time-up there is nothing left to end.)
        if self.timer_running and all(l.finished for l in self._active_lanes()):
            self.elapsed_time = now - self.start_time - self.paused
            self.last_active_time = now
            self.timer_running = False
            self.ended = True

    def lap_callback(self, lane_number, channel=None):
        """Register a line crossing on a lane (1-based number)."""
        if not isinstance(lane_number, int) or not 1 <= lane_number <= self.num_lanes:
            raise ValueError(f'lane must be between 1 and {self.num_lanes}')
        with self._lock:
            self._register_lap(self.lanes[lane_number - 1])

    def lap_callback1(self, channel=None):
        self.lap_callback(1, channel)

    def lap_callback2(self, channel=None):
        self.lap_callback(2, channel)

    def get_current_lap_times(self):
        with self._lock:
            if self.start_time is None:
                return

            now = time.time()
            for lane in self._active_lanes():
                if lane.finished:
                    lane.lap_time = None
                elif lane.last_total_time is None:
                    lane.lap_time = now - self.start_time
                else:
                    lane.lap_time = now - lane.last_total_time

    def check_finished(self):
        with self._lock:
            self._expire_if_needed(time.time())
            return all(lane.finished for lane in self._active_lanes())

    @staticmethod
    def get_formatted_time(lap_time):
        if lap_time is None:
            return '00:00:000'

        minutes = int(lap_time // 60)
        seconds = int(lap_time % 60)
        thousands = int((lap_time % 1) * 1000)
        return '{:02d}:{:02d}:{:03d}'.format(minutes, seconds, thousands)

    def _winner(self):
        """Lane number of the winner, 0 for a tie, None while undecided.

        Ranking: most laps, then the lane that crossed the line first.
        """
        lanes = [(n, l) for n, l in enumerate(self.lanes, start=1) if l.active]
        if not all(l.finished for _, l in lanes) or all(l.num_laps == 0 for _, l in lanes):
            return None
        ranked = sorted((x for x in lanes if x[1].num_laps > 0),
                        key=lambda x: (-x[1].num_laps, x[1].last_total_time))
        if (len(ranked) > 1 and ranked[0][1].num_laps == ranked[1][1].num_laps
                and ranked[0][1].last_total_time == ranked[1][1].last_total_time):
            return 0
        return ranked[0][0]

    def _race_info(self):
        """Race goal and status for the templates. Caller holds the lock."""
        info = {'mode': self.mode, 'goal_text': '', 'lap_goal': '',
                'formatted_remaining': None, 'status_text': ''}
        if self.mode == MODE_LAPS:
            info['goal_text'] = f'Race to {self.target_laps} laps'
            info['lap_goal'] = f' / {self.target_laps}'
        elif self.mode == MODE_TIME:
            info['goal_text'] = f'Time limit {self.get_formatted_time(self.time_limit)}'
            elapsed = self.elapsed_time or 0.0
            info['formatted_remaining'] = self.get_formatted_time(max(self.time_limit - elapsed, 0.0))

        winner = self._winner()
        if winner is not None:
            info['status_text'] = 'Race finished - tie' if winner == 0 else f'Race finished - winner: Lane {winner}'
        elif self.ended and self.mode == MODE_TIME:
            info['status_text'] = 'Time is up - finish your lap'
        return info

    def time(self):
        with self._lock:
            if self.start_time is None:
                formatted_time = '00:00:000'
            else:
                formatted_time = self.get_formatted_time(self.elapsed_timer())
            return {'formatted_time': formatted_time, **self._race_info()}

    def lap(self, lane_number):
        self.lap_callback(lane_number)

    def get_template_data(self):
        self.get_current_lap_times()

        with self._lock:
            zero = self.get_formatted_time(None)
            formatted_time = zero
            if self.start_time is not None:
                formatted_time = self.get_formatted_time(self.elapsed_timer())

            lanes = []
            for number, lane in enumerate(self.lanes, start=1):
                if not lane.active:
                    continue
                if self.start_time is None:
                    current = zero
                elif lane.last_lap_time is not None:
                    current = self.get_formatted_time(lane.lap_time)
                else:
                    current = formatted_time
                lanes.append({
                    'number': number,
                    'formatted_current_lap_time': current,
                    'formatted_last_lap_time': self.get_formatted_time(lane.last_lap_time),
                    'formatted_fastest_lap_time': self.get_formatted_time(lane.fastest_lap_time),
                    'num_laps': lane.num_laps,
                })

            return {
                **self._race_info(),
                'formatted_time': formatted_time,
                'lanes': lanes,
            }
