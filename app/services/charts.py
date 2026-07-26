"""Graphiques vectoriels réutilisables (radar) pour le web et le PDF."""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple


def radar_points(values: Sequence[float], cx: float, cy: float, radius: float,
                 max_value: float = 100.0) -> List[Tuple[float, float]]:
    """Coordonnées du polygone radar. Le premier axe pointe vers le haut."""
    count = len(values)
    if count == 0:
        return []
    points = []
    for index, value in enumerate(values):
        angle = math.pi / 2 - (2 * math.pi * index / count)
        ratio = max(0.0, min(1.0, float(value) / max_value if max_value else 0.0))
        points.append((cx + radius * ratio * math.cos(angle), cy + radius * ratio * math.sin(angle)))
    return points


def axis_points(count: int, cx: float, cy: float, radius: float) -> List[Tuple[float, float]]:
    return [
        (
            cx + radius * math.cos(math.pi / 2 - (2 * math.pi * i / count)),
            cy + radius * math.sin(math.pi / 2 - (2 * math.pi * i / count)),
        )
        for i in range(count)
    ]


def radar_svg(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    size: int = 420,
    color: str = "#4F46E5",
    grid_color: str = "#D8DEE9",
    label_color: str = "#475569",
    rings: int = 4,
    comparison: Sequence[float] | None = None,
    comparison_color: str = "#94A3B8",
) -> str:
    """Radar en SVG pur : aucune dépendance JavaScript, imprimable tel quel."""
    cx = cy = size / 2
    radius = size * 0.34
    count = len(labels)
    parts: List[str] = [
        f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="Radar de maturité par dimension" class="radar">'
    ]

    for ring in range(1, rings + 1):
        r = radius * ring / rings
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in axis_points(count, cx, cy, r))
        parts.append(
            f'<polygon points="{pts}" fill="none" stroke="{grid_color}" stroke-width="1" />'
        )
        parts.append(
            f'<text x="{cx + 4:.1f}" y="{cy - r + 4:.1f}" font-size="9" fill="{grid_color}">'
            f'{int(100 * ring / rings)}</text>'
        )

    for x, y in axis_points(count, cx, cy, radius):
        parts.append(
            f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y:.1f}" '
            f'stroke="{grid_color}" stroke-width="1" />'
        )

    if comparison:
        cpts = " ".join(f"{x:.1f},{y:.1f}" for x, y in radar_points(comparison, cx, cy, radius))
        parts.append(
            f'<polygon points="{cpts}" fill="none" stroke="{comparison_color}" '
            f'stroke-width="2" stroke-dasharray="5 4" />'
        )

    pts = radar_points(values, cx, cy, radius)
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    parts.append(
        f'<polygon points="{poly}" fill="{color}" fill-opacity="0.22" '
        f'stroke="{color}" stroke-width="2.5" />'
    )
    for x, y in pts:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}" />')

    for index, label in enumerate(labels):
        angle = math.pi / 2 - (2 * math.pi * index / count)
        lx = cx + (radius + 26) * math.cos(angle)
        ly = cy + (radius + 26) * math.sin(angle)
        anchor = "middle"
        if lx > cx + 8:
            anchor = "start"
        elif lx < cx - 8:
            anchor = "end"
        value = values[index] if index < len(values) else 0
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" font-size="11" '
            f'font-weight="600" fill="{label_color}">{label}</text>'
        )
        parts.append(
            f'<text x="{lx:.1f}" y="{ly + 13:.1f}" text-anchor="{anchor}" font-size="10" '
            f'fill="{color}">{value:.0f} %</text>'
        )

    parts.append("</svg>")
    return "".join(parts)
