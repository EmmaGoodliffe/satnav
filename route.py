import numpy as np
import pandas as pd
from geometry import Coord, angle_between, bearing
from matplotlib import pyplot as plt
from typing import Literal

A = np.typing.NDArray[np.float64]
FV = dict[Literal["value"] | Literal["units"], float | str]


class Instruction:
    def __init__(self, coord: Coord, text: str, distance: float, icon: str | None = None):
        self.coord = coord
        self.icon = icon
        self.text = text
        self.distance = distance

    def __repr__(self):
        return f"{self.coord} => {self.text}"

    def rel_project(self, ic: Coord):
        """project instruction relative to given initial (x, y)"""
        self.xy = self.coord.project() - ic.project()
        self.x, self.y = self.xy
        return self


class Route:
    def __init__(self, name: str, start: Coord, end: Coord, duration: float, instructions: list[Instruction]):
        self.name = name
        self.start = start
        self.end = end
        self.duration = duration
        self.instructions = [inst.rel_project(start) for inst in instructions]
        self.inst_xs = np.array([inst.x for inst in self.instructions])
        self.inst_ys = np.array([inst.y for inst in self.instructions])

    def __repr__(self):
        return f"Route {self.name}: {len(self.instructions)} instructions over {self.duration}s"

    def set_instructions_text(self, values: list[str] | pd.Series):
        for inst, text in zip(self.instructions, values):
            inst.text = text

    def set_instructions_icons(self, icons: list[str] | pd.Series):
        for inst, icon in zip(self.instructions, icons):
            inst.icon = icon

    def set_elevations(self, els: list[float] | A | pd.Series):
        for inst, el in zip(self.instructions, els):
            inst.coord.el = el

    def plot(self):
        plt.plot(self.inst_xs, self.inst_ys, "-o")
        for inst in self.instructions:
            plt.text(inst.x + 50, inst.y, inst.text)
        plt.axis("scaled")
        plt.xlabel("x [m]")
        plt.ylabel("y [m]")

    def instruct(self, me: Coord):
        me_xy = me.project() - self.start.project()
        me_x, me_y = me_xy
        dds = (self.inst_xs - me_x) ** 2 + (self.inst_ys - me_y) ** 2
        i = np.argmin(dds)
        nearest = self.instructions[i].xy
        after = self.instructions[i + 1].xy
        next_i = i + 1 if angle_between(after - nearest, me_xy - nearest).rad < np.pi / 2 else i
        prev_inst, inst, next_inst = self.instructions[next_i - 1 : next_i + 1 + 1]
        d = np.sqrt(dds[next_i])
        return {
            "i": next_i,
            "distance_until_instruction": d,
            "prev_instruction": prev_inst,
            "instruction": inst,
            "next_instruction": next_inst,
            "bearing": bearing(inst.xy - prev_inst.xy),
            "total_distance_covered_along_route": inst.distance - d,
        }
