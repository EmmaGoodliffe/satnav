import geopandas as gpd
import numpy as np
from geometry import Angle, Coord
from json import loads as load_json
from matplotlib.axes import Axes
from route import Cue, Instruction
from shapely.geometry import Point

A = np.ndarray[tuple[int], np.dtype[np.float64]]

LONG_LAT = "EPSG:4326"
MERCATOR = "EPSG:3857"


def get_val(d: dict, k: str):
    if k in d:
        return d[k]
    return None


def rotate_projected(c: Coord, angle: Angle, origin: Coord):
    return (
        gpd.GeoSeries([Point(c.long_lat("°"))])
        .set_crs(LONG_LAT)
        .to_crs(MERCATOR)
        .rotate(angle.deg, origin=tuple(origin.long_lat("°")))
    )


def closest(x: float, ys: A):
    ds = np.abs(ys - x)
    i = np.argmin(ds)
    return ys[i]


def get_radius(x: float):
    p = int(np.log10(x))
    options = np.array([[10**i / 2, 10**i] for i in range(1, p + 2)]).flatten()
    ans = closest(x, options)
    print(f"{x} => r = {ans}")
    return ans


with open("./road_styles.json", encoding="utf-8") as f:
    road_styles = load_json(f.read())
    # ['colourful' | 'grey']['pedestrian' | 'cycleway' | ...]['fclasses' | 'colour' | 'thickness']


class GpkgMap:
    def __init__(self, gdf: gpd.GeoDataFrame):
        self.gdf = gdf

    def plot_raw(self, ax: Axes, bbox: A, cues: list[Cue] = [], me: Coord | None = None, style="colourful"):
        """Plot the map in (λ, φ) coordinates"""
        # Plot roads
        for road_name, road in road_styles[style].items():
            for fclass in road["fclasses"]:
                if fclass in list(self.gdf["fclass"]):
                    self.gdf[self.gdf["fclass"] == fclass].plot(
                        ax=ax,
                        color=road["colour"],
                        linewidth=road["thickness"],
                        label=road_name,
                    )
        # Plot me
        if me is not None:
            ax.plot(*me.long_lat("°"), "o", label="me")
        # Plot cues
        for cue in cues:
            ax.plot(*cue.coord.long_lat("°"), "o", c="k", label="cue")
        # Aesthetics
        xlims, ylims = bbox.reshape(2, 2).T
        ax.set_xlim(*xlims)
        ax.set_ylim(*ylims)
        leg = {label: handle for handle, label in zip(*ax.get_legend_handles_labels())}
        ax.legend(leg.values(), leg.keys())

    def plot_instruction(
        # self, ax: Axes, angle: Angle, origin: Coord, cues: list[Cue] = [], me: Coord | None = None, style="colourful"
        self,
        ax: Axes,
        instruction: Instruction,
        style="colourful",
        legend=False,
    ):
        """Plot an instruction on the map in projected and rotated (x, y) coordinates"""
        angle = instruction.bearing
        # Plot roads
        # if monochrome:
        #     self.gdf.to_crs(MERCATOR).rotate(angle.deg, origin=tuple(origin.long_lat("°"))).plot(
        #         ax=ax, color="k", alpha=0.5
        #     )
        # else:
        for road_name, road in road_styles[style].items():
            for fclass in road["fclasses"]:
                if fclass in list(self.gdf["fclass"]):
                    self.gdf[self.gdf["fclass"] == fclass].to_crs(MERCATOR).rotate(
                        angle.deg, origin=tuple(instruction.origin.long_lat("°"))
                    ).plot(
                        ax=ax,
                        color=road["colour"],
                        linewidth=road["thickness"],
                        label=road_name,
                        linestyle=get_val(road, "style") or "-",
                    )
        # Plot cues
        for cue in instruction.route.cues:
            rotate_projected(cue.coord, angle, instruction.origin).plot(ax=ax, c="k", label="cue")
        # Plot origin
        projected_origin = rotate_projected(instruction.origin, angle, instruction.origin)
        projected_origin.plot(ax=ax, label="origin")
        # Aesthetics
        radius = get_radius(instruction.dist_until_cue)
        ax.set_xlim(projected_origin.x[0] - (radius * 128 / 296), projected_origin.x[0] + (radius * 128 / 296))
        ax.set_ylim(projected_origin.y[0] - (radius), projected_origin.y[0] + (radius))
        ax.set_axis_off()
        if legend:
            leg = {label: handle for handle, label in zip(*ax.get_legend_handles_labels())}
            ax.legend(leg.values(), leg.keys())
