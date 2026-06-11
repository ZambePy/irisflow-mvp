"""HeuristicFilter — port direto do GazeFollower (gazefollower/filter/HeuristicFilter.py)."""
import numpy as np


class HeuristicFilter:
    def __init__(self, look_ahead: int = 3) -> None:
        self.raw_x: list[float] = []
        self.raw_y: list[float] = []
        self.dummy_x: float = np.nan
        self.dummy_y: float = np.nan
        self.look_ahead = look_ahead

    def filter_values(self, x: float, y: float) -> tuple[float, float]:
        self.do_filter(True, x)
        self.do_filter(False, y)
        if np.isnan(self.dummy_x) or np.isnan(self.dummy_y):
            return x, y
        return self.dummy_x, self.dummy_y

    def do_filter(self, is_x: bool, element: float) -> None:
        raw = self.raw_x if is_x else self.raw_y
        raw.append(element)

        if len(raw) == self.look_ahead * 2 + 1:
            c = self.look_ahead  # center index
            for nv in range(1, self.look_ahead + 1):
                if raw[c] > raw[c - nv] and raw[c] > raw[c + nv]:
                    raw[c] = raw[c - 1]
                elif raw[c] < raw[c - nv] and raw[c] < raw[c + nv]:
                    raw[c] = raw[c - 1]

            if is_x:
                self.dummy_x = raw[c]
            else:
                self.dummy_y = raw[c]

            raw.pop(0)

    def reset(self) -> None:
        self.raw_x = []
        self.raw_y = []
        self.dummy_x = np.nan
        self.dummy_y = np.nan
