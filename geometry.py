import numpy as np

A = np.typing.NDArray[np.float64]


class Angle:
    """Angle that can easily be converted between radians and degrees"""

    def __init__(self, rad=0.0, deg=0.0):
        if rad and deg:
            raise Exception("simultaneously specified angle in radians and degrees")
        elif rad:
            self.rad = rad
            self.deg = rad * 180 / np.pi
        else:
            self.deg = deg
            self.rad = deg * np.pi / 180

    def __repr__(self):
        return f"{self.deg:.4f}°"

    def to(self, units: str):
        if units in ["rad", "radian", "radians"]:
            return self.rad
        elif units in ["°", "degree", "degrees"]:
            return self.deg
        raise Exception(f"unknown units: {units}")


class Coord:
    """Coordinate in terms of latitude and longitude"""

    def __init__(self, lat: Angle, long: Angle, el: float | None = None):
        self.lat = lat
        self.long = long
        self.el = el

    def __repr__(self):
        return f"(φ = {self.lat}, λ = {self.long})"

    def project(self):
        """project onto 2D pane"""
        R = 6378137
        x = R * self.long.rad
        y = R * np.log(np.tan((np.pi / 4) + (self.lat.rad / 2)))
        return np.array([x, y])

    def lat_long(self, units: str):
        return np.array([self.lat.to(units), self.long.to(units)])

    def long_lat(self, units: str):
        return np.array([self.long.to(units), self.lat.to(units)])


def angle_between(v1: A, v2: A):
    """Smallest angle between two vectors"""
    return Angle(rad=np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))))


def bearing(v: A):
    """Clockwise angle between vector and North"""
    x, y = v
    return Angle(rad=(np.pi / 2) - np.arctan(y / x))


def rotate_vec(v: A, theta: Angle, origin=[0, 0]):
    """Rotate `v` clockwise by angle `theta` about `origin`"""
    c, s = np.cos(theta.rad), np.sin(theta.rad)
    mat = np.array([[c, -s], [s, c]])
    vec = v.reshape(2, 1)
    origin_vec = np.array(origin).reshape(2, 1)
    rotated_vec = (mat @ (vec - origin_vec)) + origin_vec
    return rotated_vec.reshape(2)
