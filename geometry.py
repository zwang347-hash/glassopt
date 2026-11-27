"""Geometry for a single strictly convex pane. Lengths are in millimeters."""

import math
from dataclasses import dataclass

Point = tuple[float, float]
VERTICES = "ABCDE"
EPSILON = 1e-12


@dataclass(frozen=True)
class Rectangle:
    angle: float
    left: float
    bottom: float
    right: float
    top: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.top - self.bottom

    @property
    def area(self) -> float:
        return self.width * self.height

    def project(self, point: Point) -> Point:
        x, y = point
        cosine, sine = math.cos(self.angle), math.sin(self.angle)
        return x * cosine + y * sine, -x * sine + y * cosine


@dataclass(frozen=True)
class GlassPlan:
    points: tuple[Point, ...]
    tight: Rectangle
    stock: Rectangle
    glass_area: float

    @property
    def scrap_area(self) -> float:
        return max(0.0, self.stock.area - self.glass_area)

    @property
    def efficiency(self) -> float:
        return self.glass_area / self.stock.area


def generate_points(sides, diagonals=()) -> tuple[Point, ...]:
    """Reconstruct AB, BC, …, last-to-A with internal diagonals AC, then AD."""
    sides, diagonals = tuple(sides), tuple(diagonals)
    n = len(sides)
    if n not in (3, 4, 5) or len(diagonals) != n - 3:
        raise ValueError("请输入 3–5 条边，以及对应数量的 A 点对角线。")

    labels = [VERTICES[i] + VERTICES[(i + 1) % n] for i in range(n)]
    labels.extend("A" + VERTICES[i] for i in range(2, n - 1))
    for label, length in zip(labels, sides + diagonals):
        if not math.isfinite(length) or length <= 0:
            raise ValueError(f"{label} 必须是大于 0 的有限数值。")

    scale = max(sides + diagonals)
    radii = (sides[0], *diagonals, sides[-1])
    points = [(0.0, 0.0), (sides[0] / scale, 0.0)]
    angle = 0.0
    for i in range(1, n - 1):
        a, b, c = radii[i - 1] / scale, radii[i] / scale, sides[i] / scale
        # Half-angle formula avoids subtracting nearly equal squared lengths.
        lower_gap = c - abs(a - b)
        upper_gap = a + b - c
        if min(lower_gap, upper_gap) <= EPSILON:
            triangle = "A" + VERTICES[i:i + 2]
            raise ValueError(f"三角形 {triangle} 的尺寸无法闭合，或过于接近退化。")
        angle += 2 * math.atan2(
            math.sqrt(lower_gap * (c + abs(a - b))),
            math.sqrt(upper_gap * (a + b + c)),
        )
        radius = radii[i] / scale
        points.append((radius * math.cos(angle), radius * math.sin(angle)))

    if angle >= math.pi - EPSILON:
        raise ValueError("A 点的内角必须小于 180°，请核对边和对角线的顺序及尺寸。")

    for i in range(n):
        a, b, c = points[i - 1], points[i], points[(i + 1) % n]
        ux, uy = b[0] - a[0], b[1] - a[1]
        vx, vy = c[0] - b[0], c[1] - b[1]
        if ux * vy - uy * vx <= EPSILON * math.hypot(ux, uy) * math.hypot(vx, vy):
            raise ValueError(f"{VERTICES[i]} 点处无法形成严格凸角，请核对尺寸及顶点顺序。")
    return tuple((x * scale, y * scale) for x, y in points)


def polygon_area(points: tuple[Point, ...]) -> float:
    terms = (
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1])
    )
    return abs(math.fsum(terms)) / 2


def min_rectangle(points: tuple[Point, ...], margin: float = 0.0) -> Rectangle:
    """Return tight bounds at the orientation minimizing padded stock area."""
    candidates = []
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        angle = math.atan2(y2 - y1, x2 - x1)
        cosine, sine = math.cos(angle), math.sin(angle)
        xs = [x * cosine + y * sine for x, y in points]
        ys = [-x * sine + y * cosine for x, y in points]
        candidates.append(Rectangle(angle, min(xs), min(ys), max(xs), max(ys)))

    # Between support-vertex changes, each projected span is a positive
    # sinusoid and is concave. The log of padded area is therefore concave,
    # so a minimum occurs at a boundary (an edge-aligned orientation).
    return min(candidates, key=lambda r: (r.width + 2 * margin) * (r.height + 2 * margin))


def calculate_plan(sides, diagonals=(), margin: float = 0.0) -> GlassPlan:
    if not math.isfinite(margin) or margin < 0:
        raise ValueError("单侧余量必须是大于或等于 0 的有限数值。")
    points = generate_points(sides, diagonals)
    # Keep squared dimensions representable in floating point arithmetic.
    largest = max(margin, *(abs(v) for point in points for v in point))
    if not 1e-140 <= largest <= 1e140:
        raise ValueError("尺寸超出数值计算范围，请检查输入单位。")
    tight = min_rectangle(points, margin)
    stock = Rectangle(tight.angle, tight.left - margin, tight.bottom - margin,
                      tight.right + margin, tight.top + margin)
    glass_area = polygon_area(points)
    if glass_area <= 0 or stock.area <= 0:
        raise ValueError("成品尺寸超出数值计算范围，请检查输入单位。")
    return GlassPlan(points, tight, stock, glass_area)
