import geopandas as gpd
import numpy as np
from geometry import Angle, Coord
from json import loads as load_json
from matplotlib.axes import Axes
from route import Cue
from shapely.geometry import Point

A = np.typing.NDArray[np.float64]

LONG_LAT = "EPSG:4326"
MERCATOR = "EPSG:3857"

with open("./roads_styles.json", encoding="utf-8") as f:
    roads_data = load_json(f.read())


def rotate_projected(c: Coord, angle: Angle, origin: Coord):
    og = tuple(origin.long_lat("°"))
    return gpd.GeoSeries([Point(c.long_lat("°"))]).set_crs(LONG_LAT).to_crs(MERCATOR).rotate(angle.deg, origin=og)


class GpkgMap:
    def __init__(self, gdf: gpd.GeoDataFrame):
        self.gdf = gdf

    def plot_raw(self, ax: Axes, bbox: A, me: Coord | None = None, cues: list[Cue] = []):
        """Plot the map in (λ, φ) coordinates"""
        # Plot roads
        for road_name, road in roads_data.items():
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

    def plot_rotated(self, ax: Axes, angle: Angle, origin: Coord, me: Coord | None = None, cues: list[Cue] = []):
        """Plot the map in projected and rotated (x, y) coordinates"""
        # Plot roads
        # self.gdf.to_crs(MERCATOR).rotate(angle.deg, origin=tuple(origin.long_lat("°"))).plot(
        #     ax=ax, color="k", alpha=0.5
        # )
        for road_name, road in roads_data.items():
            for fclass in road["fclasses"]:
                if fclass in list(self.gdf["fclass"]):
                    self.gdf[self.gdf["fclass"] == fclass].to_crs(MERCATOR).rotate(
                        angle.deg, origin=tuple(origin.long_lat("°"))
                    ).plot(
                        ax=ax,
                        color=road["colour"],
                        linewidth=road["thickness"],
                        label=road_name,
                    )
        # Plot cues
        for cue in cues:
            rotate_projected(cue.coord, angle, origin).plot(ax=ax, c="k", label="cue")
        if me is not None:
            # Plot me
            projected_me = rotate_projected(me, angle, origin)
            projected_me.plot(ax=ax, label="me")
            rotate_projected(origin, angle, origin).plot(ax=ax, label="origin")
            # Aesthetics
            ax.set_xlim(projected_me.x[0] - 250, projected_me.x[0] + 250)
            ax.set_ylim(projected_me.y[0] - 100, projected_me.y[0] + 400)
        leg = {label: handle for handle, label in zip(*ax.get_legend_handles_labels())}
        ax.legend(leg.values(), leg.keys())
