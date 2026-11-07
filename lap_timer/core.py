import time
from dataclasses import dataclass
from threading import Lock

from .config import MIN_LAP_SECONDS


@dataclass
class LaneState:
    finished: bool = False
    last_total_time: float | None = None
    lap_time: float | None = None
    last_lap_time: float | None = None
    fastest_lap_time: float | None = None
    num_laps: int = 0


MODE_LAPS = 'laps'
MODE_TIME = 'time'
MAX_LAPS = 999
MAX_TIME_SECONDS = 4 * 3600


class LapTimer:
    def __init__(self):
        self._lock = Lock()
        self.reset()

    def reset(self):
        with self._lock:
            self.timer_running = False
            self.start_time = None
            self.last_active_time = None
            self.paused = 0.0
            self.elapsed_time = None
            self.lane1 = LaneState()
            self.lane2 = LaneState()
            # race configuration: mode None means a free-running timer
            self.mode = None
            self.target_laps = None
            self.time_limit = None
            # True once the race condition (lap target / time limit) ended the race
            self.ended = False

    @property
    def configured(self):
        return self.mode is not None

    def configure(self, mode, laps=None, time_seconds=None):
        """Select the race condition. Only allowed before the race has started."""
        with self._lock:
            if self.start_time is not None:
                raise ValueError('race already started, reset first')
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
                self.lane1.finished = self._reached_target(self.lane1)
                self.lane2.finished = self._reached_target(self.lane2)

    def continue_timer(self):
        with self._lock:
            if (not self.timer_running and not self.ended
                    and self.start_time is not None and self.last_active_time is not None):
                self.timer_running = True
                self.paused += time.time() - self.last_active_time
                self.lane1.finished = self._reached_target(self.lane1)
                self.lane2.finished = self._reached_target(self.lane2)

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
        if lane.finished:
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
        if self.lane1.finished and self.lane2.finished and self.timer_running:
            self.elapsed_time = now - self.start_time - self.paused
            self.last_active_time = now
            self.timer_running = False
            self.ended = True

    def lap_callback1(self, channel=None):
        with self._lock:
            self._register_lap(self.lane1)

    def lap_callback2(self, channel=None):
        with self._lock:
            self._register_lap(self.lane2)

    def get_current_lap_times(self):
        with self._lock:
            if self.start_time is None:
                return

            now = time.time()

            if not self.lane1.finished:
                if self.lane1.last_total_time is None:
                    self.lane1.lap_time = now - self.start_time
                else:
                    self.lane1.lap_time = now - self.lane1.last_total_time
            else:
                self.lane1.lap_time = None

            if not self.lane2.finished:
                if self.lane2.last_total_time is None:
                    self.lane2.lap_time = now - self.start_time
                else:
                    self.lane2.lap_time = now - self.lane2.last_total_time
            else:
                self.lane2.lap_time = None

    def check_finished(self):
        with self._lock:
            self._expire_if_needed(time.time())
            return self.lane1.finished and self.lane2.finished

    @staticmethod
    def get_formatted_time(lap_time):
        if lap_time is None:
            return '00:00:000'

        minutes = int(lap_time // 60)
        seconds = int(lap_time % 60)
        thousands = int((lap_time % 1) * 1000)
        return '{:02d}:{:02d}:{:03d}'.format(minutes, seconds, thousands)

    def _winner(self):
        """Lane number (1/2) of the winner, 0 for a tie, None while undecided."""
        l1, l2 = self.lane1, self.lane2
        if not (l1.finished and l2.finished) or (l1.num_laps == 0 and l2.num_laps == 0):
            return None
        if l1.num_laps != l2.num_laps:
            return 1 if l1.num_laps > l2.num_laps else 2
        if l1.last_total_time == l2.last_total_time:
            return 0
        return 1 if l1.last_total_time < l2.last_total_time else 2

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

    def lap1(self):
        self.lap_callback1()

    def lap2(self):
        self.lap_callback2()

    def get_template_data(self):
        self.get_current_lap_times()

        with self._lock:
            formatted_time = '00:00:000'
            formatted_current_lap_time1 = '00:00:000'
            formatted_current_lap_time2 = '00:00:000'

            if self.start_time is not None:
                formatted_time = self.get_formatted_time(self.elapsed_timer())
                if self.lane1.last_lap_time is not None:
                    formatted_current_lap_time1 = self.get_formatted_time(self.lane1.lap_time)
                else:
                    formatted_current_lap_time1 = formatted_time

                if self.lane2.last_lap_time is not None:
                    formatted_current_lap_time2 = self.get_formatted_time(self.lane2.lap_time)
                else:
                    formatted_current_lap_time2 = formatted_time

            if self.lane1.last_lap_time is not None:
                formatted_last_lap_time1 = self.get_formatted_time(self.lane1.last_lap_time)
            else:
                formatted_last_lap_time1 = '00:00:000'

            if self.lane1.fastest_lap_time is not None:
                formatted_fastest_lap_time1 = self.get_formatted_time(self.lane1.fastest_lap_time)
            else:
                formatted_fastest_lap_time1 = '00:00:000'

            if self.lane2.last_lap_time is not None:
                formatted_last_lap_time2 = self.get_formatted_time(self.lane2.last_lap_time)
            else:
                formatted_last_lap_time2 = '00:00:000'

            if self.lane2.fastest_lap_time is not None:
                formatted_fastest_lap_time2 = self.get_formatted_time(self.lane2.fastest_lap_time)
            else:
                formatted_fastest_lap_time2 = '00:00:000'

            return {
                **self._race_info(),
                'formatted_time': formatted_time,
                'formatted_current_lap_time1': formatted_current_lap_time1,
                'formatted_last_lap_time1': formatted_last_lap_time1,
                'formatted_fastest_lap_time1': formatted_fastest_lap_time1,
                'num_laps1': self.lane1.num_laps,
                'formatted_current_lap_time2': formatted_current_lap_time2,
                'formatted_last_lap_time2': formatted_last_lap_time2,
                'formatted_fastest_lap_time2': formatted_fastest_lap_time2,
                'num_laps2': self.lane2.num_laps,
            }
