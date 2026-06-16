import numpy as np
import pandas as pd
from fit_tool.fit_file import FitFile
from geometry import Angle, Coord
from route import Cue, Route
from typing import Literal

A = np.typing.NDArray[np.float64]
FV = dict[Literal["value"] | Literal["units"], float | str]


def fv_to_sec(x: FV) -> float:
    """convert fit value to number in seconds"""
    if x["units"] == "s":
        return float(x["value"])
    if x["units"] == "ms":
        return float(x["value"]) * 1e-3
    raise Exception(f"unknown units: {x['units']}")


def fv_to_coord(lat: FV, long: FV, el: float | None = None):
    """convert fit value to coordinate"""
    if lat["units"] != "degrees" or long["units"] != "degrees":
        raise Exception(f"unexpected units")
    return Coord(Angle(deg=float(lat["value"])), Angle(deg=float(long["value"])))


def fit_to_df(path: str):
    df = pd.DataFrame(FitFile.from_file("stav_to_trin.fit").to_rows())
    df.columns = df.iloc[0]
    df = df.iloc[1:]
    return df


def fit_to_json(path: str):
    """
    when used with `fit` file from RwGPS, JSON is:
    - `file_id.0`: ...
    - `course.0.name.value`
    - `lap.0`:
        - `timestamp`
        - `total_elapsed_time`
        - `start/end_position_lat/long`
    - `event`: ...
    - `course_point.i`:
        - `timestamp`
        - `position_lat/long`
    - `record`: ...
    """
    df = fit_to_df(path)
    json = {m: [] for m in df["Message"]}
    num_fields = max([int(c[len("Field") :]) for c in df.columns if c.startswith("Field")])
    for i in range(df.shape[0]):
        x = df.iloc[i]
        if x["Type"] == "Data":
            item = {}
            for n in range(num_fields):
                item[x[f"Field {n}"]] = {"value": x[f"Value {n}"], "units": x[f"Units {n}"]}
            json[x["Message"]].append(item)
    return json


def fit_to_route(path: str):
    json = fit_to_json(path)
    return Route(
        json["course"][0]["name"]["value"],
        fv_to_coord(
            json["lap"][0]["start_position_lat"],
            json["lap"][0]["start_position_long"],
        ),
        fv_to_coord(json["lap"][0]["end_position_lat"], json["lap"][0]["end_position_long"]),
        fv_to_sec(json["lap"][0]["total_elapsed_time"]),
        [
            Cue(
                fv_to_coord(cp["position_lat"], cp["position_long"]),
                cp["name"]["value"],
                cp["distance"]["value"],
            )
            for cp in json["course_point"]
        ],
    )
