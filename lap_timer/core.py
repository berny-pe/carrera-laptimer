import time
from dataclasses import dataclass
from threading import Lock


@dataclass
class LaneState:
    finished: bool = False
    last_total_time: float | None = None
    lap_time: float | None = None
    last_lap_time: float | None = None
    fastest_lap_time: float | None = None
    num_laps: int = 0


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

    def start_timer(self):
        with self._lock:
            if not self.timer_running:
                self.timer_running = True
                self.start_time = time.time()
                self.last_active_time = None
                self.paused = 0.0
                self.lane1.finished = False
                self.lane2.finished = False

    def continue_timer(self):
        with self._lock:
            if not self.timer_running and self.start_time is not None and self.last_active_time is not None:
                self.timer_running = True
                self.paused += time.time() - self.last_active_time
                self.lane1.finished = False
                self.lane2.finished = False

    def stop_timer(self):
        with self._lock:
            self.last_active_time = time.time()
            if self.timer_running:
                self.elapsed_timer()
                self.timer_running = False

    def elapsed_timer(self):
        if self.timer_running and self.start_time is not None:
            self.elapsed_time = time.time() - self.start_time - self.paused
        return self.elapsed_time

    def _register_lap(self, lane: LaneState):
        if lane.finished:
            return

        if self.start_time is None:
            return

        now = time.time()
        if lane.last_total_time is not None:
            lane.last_lap_time = now - lane.last_total_time
        else:
            lane.last_lap_time = now - self.start_time

        if lane.fastest_lap_time is None or lane.last_lap_time < lane.fastest_lap_time:
            lane.fastest_lap_time = lane.last_lap_time

        lane.num_laps += 1
        lane.last_total_time = now

        if not self.timer_running:
            lane.finished = True

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
            return self.lane1.finished and self.lane2.finished

    @staticmethod
    def get_formatted_time(lap_time):
        if lap_time is None:
            return '00:00:000'

        minutes = int(lap_time // 60)
        seconds = int(lap_time % 60)
        thousands = int((lap_time % 1) * 1000)
        return '{:02d}:{:02d}:{:03d}'.format(minutes, seconds, thousands)

    def time(self):
        with self._lock:
            if self.start_time is None:
                formatted_time = '00:00:000'
            else:
                formatted_time = self.get_formatted_time(self.elapsed_timer())
            return {'formatted_time': formatted_time}

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
