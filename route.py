import numpy as np
import pandas as pd
from geometry import Coord, angle_between, bearing
from matplotlib import pyplot as plt
from typing import Literal

A = np.ndarray[tuple[int], np.dtype[np.float64]]
FV = dict[Literal["value"] | Literal["units"], float | str]


def first_exceeding(x: float, ys: A):
    ys[ys < x] = np.inf
    i = np.argmin(ys)
    return ys[i]


def get_radius(x: float) -> float:
    p = int(np.log10(x))
    options = np.array([[10**i / 2, 10**i] for i in range(1, p + 2)]).flatten()
    ans = first_exceeding(x, options)
    print(f"{x} => r = {ans}")
    return ans


class Cue:
    def __init__(self, coord: Coord, text: str, distance: float, icon: str | None = None):
        self.coord = coord
        self.icon = icon
        self.text = text
        self.distance = distance

    def __repr__(self):
        return f"{self.coord} => {self.text}"

    def rel_project(self, ic: Coord):
        """project cue relative to given initial (x, y)"""
        self.xy = self.coord.project() - ic.project()
        self.x, self.y = self.xy
        return self


class Instruction:
    def __init__(self, route: Route, cue_i: int, dist_until_cue: float):
        self.route = route
        self.prev_cue, self.cue, self.next_cue = route.cues[cue_i - 1 : cue_i + 1 + 1]
        self.dist_until_cue = dist_until_cue  # m
        self.radius = get_radius(dist_until_cue)
        if dist_until_cue > 1e3:
            self.origin = (self.prev_cue.coord + self.cue.coord) / 2
        else:
            self.origin = self.cue.coord
        self.bearing = bearing(self.cue.xy - self.prev_cue.xy)
        self.total_distance_covered_along_route = self.cue.distance - dist_until_cue

    def __repr__(self):
        return f"in {self.dist_until_cue:.0f}m: {self.cue}"


class Route:
    def __init__(self, name: str, start: Coord, end: Coord, duration: float, cues: list[Cue]):
        self.name = name
        self.start = start
        self.end = end
        self.duration = duration
        self.cues = [cue.rel_project(start) for cue in cues]
        self.cue_xs = np.array([cue.x for cue in self.cues])
        self.cue_ys = np.array([cue.y for cue in self.cues])

    def __repr__(self):
        return f"Route {self.name}: {len(self.cues)} cues over {self.duration}s"

    def set_cues_text(self, values: list[str] | pd.Series):
        for cue, text in zip(self.cues, values):
            cue.text = text

    def set_cues_icons(self, icons: list[str] | pd.Series):
        for cue, icon in zip(self.cues, icons):
            cue.icon = icon

    def set_elevations(self, els: list[float] | A | pd.Series):
        for cue, el in zip(self.cues, els):
            cue.coord.el = el

    def plot(self):
        plt.plot(self.cue_xs, self.cue_ys, "-o")
        for cue in self.cues:
            plt.text(cue.x + 50, cue.y, cue.text)
        plt.axis("scaled")
        plt.xlabel("x [m]")
        plt.ylabel("y [m]")

    def instruct(self, me: Coord):
        me_xy = me.project() - self.start.project()
        me_x, me_y = me_xy
        dds = (self.cue_xs - me_x) ** 2 + (self.cue_ys - me_y) ** 2
        i = np.argmin(dds)
        nearest = self.cues[i].xy
        after = self.cues[i + 1].xy
        next_i = i + 1 if angle_between(after - nearest, me_xy - nearest).rad < np.pi / 2 else i
        d = np.sqrt(dds[next_i])
        return Instruction(self, int(next_i), d)
