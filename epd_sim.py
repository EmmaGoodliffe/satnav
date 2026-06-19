import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import ListedColormap

Ints = np.ndarray[tuple[int], np.dtype[np.int64]]


def assert_int(x: int | float):
    if x != int(x):
        raise Exception(f"{x} is not int")
    return int(x)


def assert_not_none[T](x: T | None) -> T:
    if x is None:
        raise Exception("it was None")
    return x


def from_bit_sequences(sequences: np.ndarray[tuple[int, int], np.dtype[np.uint8]]) -> Ints:
    """e.g. `[[0, 0], [0, 1], [1, 1]]` -> `[0b00, 0b01, 0b11]`"""
    w = 1 << np.arange(sequences.shape[-1] - 1, -1, -1)  # e.g. 4, 2, 1
    return np.dot(sequences, w)


def to_bit_sequence(x: int):
    """e.g. `12` -> `[1, 1, 0, 0]`"""
    w = np.arange(int(np.log2(x)), -1, -1)
    return np.array((x & (1 << w)) > 0, dtype=np.int64)


def to_bit_sequences(l: int, xs: Ints):
    """e.g. `[3, 2]` -> `[[1, 1], [1, 0]]` when `l = 2`"""
    if len(xs.shape) != 1:
        raise Exception(f"xs are supposed to be 1D; received shape {xs.shape}")
    w = np.arange(l - 1, -1, -1)
    return np.array((xs.reshape(len(xs), 1) & (1 << w)) > 0, dtype=np.int64)


class Epd_Sim:
    # Black: 00b = 0
    # Dark Grey: 10b = 2
    # Light Grey: 01b = 1
    # White: 11b = 3

    # four white: 11111111 = FF = 255
    def __init__(self):
        self.width = 128
        self.height = 296
        self.buffer = bytearray([255] * assert_int(self.width * self.height / 4))

    def set_pixels(self, pixels: Ints):
        bit_pairs = to_bit_sequences(2, pixels.reshape(self.height * self.width))
        bits = bit_pairs.flatten()
        self.buffer = np.packbits(bits)

    def display(self, ax: Axes):
        bits = np.unpackbits(self.buffer)  # type: ignore
        bit_pairs = bits.reshape((len(bits) // 2, 2))  # e.g. [[0, 0], [0, 1], ...]
        bit_pairs = bit_pairs[:, ::-1]  # reverse pairs for ease of colours
        pixels = from_bit_sequences(bit_pairs).reshape(self.height, self.width)
        mesh = ax.pcolormesh(pixels, cmap=ListedColormap(["#222", "#555", "#bbb", "#eee"]))
        cbar = assert_not_none(ax.get_figure()).colorbar(mesh)
        cbar.set_ticks([0, 1, 2, 3])
        ax.yaxis.set_inverted(True)
        ax.set_aspect("equal")
