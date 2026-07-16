from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.utils.constants import CORE_HABIT_ORDER, HabitType

BG = (242, 242, 247)
CARD = (255, 255, 255)
TITLE = (28, 28, 30)
SECONDARY = (142, 142, 147)
GRID = (235, 235, 240)
TRACK = (245, 245, 247)
REST_FILL = (199, 199, 204)
REST_ACCENT = (142, 142, 147)

HABIT_COLORS: dict[str, tuple[int, int, int]] = {
    HabitType.CODING: (10, 132, 255),
    HabitType.MONEY: (48, 209, 88),
    HabitType.WORKOUT: (255, 159, 10),
}

HABIT_LABELS: dict[str, str] = {
    HabitType.CODING: "1",
    HabitType.MONEY: "2",
    HabitType.WORKOUT: "3",
}

WEEKDAYS_RU = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    names = (
        ["DejaVuSans-Bold.ttf", "Arial Bold.ttf"]
        if bold
        else ["DejaVuSans.ttf", "Arial.ttf", "Arial Unicode.ttf"]
    )
    roots = [
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/System/Library/Fonts/Supplemental"),
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts"),
    ]
    for root in roots:
        for name in names:
            path = root / name
            if path.exists():
                try:
                    return ImageFont.truetype(str(path), size=size)
                except OSError:
                    continue
    return ImageFont.load_default()


def render_activity_chart(
    series: list[dict],
    *,
    title: str = "Активность",
    subtitle: str | None = None,
    habit_labels: dict[str, str] | None = None,
) -> bytes:
    """Недельный график: столбики по дням, отдых отмечен отдельно."""
    scale = 2
    width, height = 1170 * scale, 980 * scale
    margin_x = 72 * scale
    chart_top = 210 * scale
    chart_bottom = height - 320 * scale

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        (40 * scale, 40 * scale, width - 40 * scale, height - 40 * scale),
        radius=36 * scale,
        fill=CARD,
    )

    font_title = _load_font(48 * scale, bold=True)
    font_sub = _load_font(28 * scale)
    font_axis = _load_font(22 * scale)
    font_legend = _load_font(24 * scale)
    font_big = _load_font(56 * scale, bold=True)
    font_rest = _load_font(18 * scale)

    draw.text((margin_x, 68 * scale), title, font=font_title, fill=TITLE)
    if subtitle:
        draw.text((margin_x, 128 * scale), subtitle, font=font_sub, fill=SECONDARY)

    work_items = [item for item in series if not item.get("is_rest")]
    totals = [int(item.get("total", 0)) for item in work_items]
    avg = (sum(totals) / len(totals)) if totals else 0.0
    summary = f"{avg:.1f}"
    summary_w = draw.textlength(summary, font=font_big)
    draw.text((width - margin_x - summary_w, 62 * scale), summary, font=font_big, fill=TITLE)
    label = "в среднем"
    label_w = draw.textlength(label, font=font_sub)
    draw.text((width - margin_x - label_w, 128 * scale), label, font=font_sub, fill=SECONDARY)

    chart_left = margin_x
    chart_right = width - margin_x
    chart_height = chart_bottom - chart_top
    max_stack = len(CORE_HABIT_ORDER)

    for level in range(1, max_stack + 1):
        y = chart_bottom - int(chart_height * (level / max_stack))
        for dx in range(0, chart_right - chart_left, 6 * scale):
            x1 = chart_left + dx
            x2 = min(x1 + 3 * scale, chart_right)
            draw.line((x1, y, x2, y), fill=GRID, width=max(2, scale))

    n = max(len(series), 1)
    gap = 28 * scale
    usable = chart_right - chart_left
    bar_w = max(36 * scale, int((usable - gap * (n - 1)) / n))
    total_bars = n * bar_w + (n - 1) * gap
    start_x = chart_left + (usable - total_bars) // 2
    radius = max(12 * scale, bar_w // 2)

    for i, item in enumerate(series):
        x0 = start_x + i * (bar_w + gap)
        day: date = item["day"]
        parts: dict = item.get("parts") or {}
        is_rest = bool(item.get("is_rest"))
        cx = x0 + bar_w / 2

        draw.rounded_rectangle(
            (x0, chart_top, x0 + bar_w, chart_bottom),
            radius=radius,
            fill=TRACK,
        )

        if is_rest:
            # вся шкала — цвет отдыха
            draw.rounded_rectangle(
                (x0, chart_top, x0 + bar_w, chart_bottom),
                radius=radius,
                fill=REST_FILL,
            )
            rest_label = "отдых"
            rw = draw.textlength(rest_label, font=font_rest)
            draw.text(
                (cx - rw / 2, chart_bottom + 16 * scale),
                rest_label,
                font=font_rest,
                fill=REST_ACCENT,
            )
            day_label = str(day.day)
            dw = draw.textlength(day_label, font=font_axis)
            draw.text(
                (x0 + (bar_w - dw) / 2, chart_bottom + 40 * scale),
                day_label,
                font=font_axis,
                fill=SECONDARY,
            )
        else:
            active = [t for t in CORE_HABIT_ORDER if parts.get(t)]
            if active:
                seg_h = chart_height // max_stack
                stack_h = seg_h * len(active)
                bar_img = Image.new("RGBA", (bar_w, chart_height), (0, 0, 0, 0))
                bar_draw = ImageDraw.Draw(bar_img)
                y_c = chart_height
                for habit_type in CORE_HABIT_ORDER:
                    if habit_type not in active:
                        continue
                    color = HABIT_COLORS.get(habit_type, (10, 132, 255))
                    bar_draw.rectangle((0, y_c - seg_h, bar_w, y_c), fill=(*color, 255))
                    y_c -= seg_h
                mask = Image.new("L", (bar_w, chart_height), 0)
                ImageDraw.Draw(mask).rounded_rectangle(
                    (0, chart_height - stack_h, bar_w, chart_height),
                    radius=radius,
                    fill=255,
                )
                bar_img.putalpha(mask)
                img.paste(bar_img, (x0, chart_top), bar_img)

            wd = WEEKDAYS_RU[day.weekday()]
            lw = draw.textlength(wd, font=font_axis)
            draw.text(
                (x0 + (bar_w - lw) / 2, chart_bottom + 16 * scale),
                wd,
                font=font_axis,
                fill=SECONDARY,
            )
            day_label = str(day.day)
            dw = draw.textlength(day_label, font=font_axis)
            color = TITLE if i == n - 1 else SECONDARY
            draw.text(
                (x0 + (bar_w - dw) / 2, chart_bottom + 44 * scale),
                day_label,
                font=font_axis,
                fill=color,
            )

    labels = habit_labels or HABIT_LABELS
    legend_items: list[tuple[tuple[int, int, int], str]] = [
        (HABIT_COLORS[habit_type], labels.get(habit_type, HABIT_LABELS[habit_type]))
        for habit_type in CORE_HABIT_ORDER
    ]
    legend_items.append((REST_FILL, "Отдых"))

    legend_y = chart_bottom + 96 * scale
    row_h = 40 * scale
    dot = 18 * scale
    for i, (color, name) in enumerate(legend_items):
        y = legend_y + i * row_h
        draw.ellipse(
            (margin_x, y + 4 * scale, margin_x + dot, y + 4 * scale + dot),
            fill=color,
        )
        draw.text(
            (margin_x + dot + 16 * scale, y),
            name,
            font=font_legend,
            fill=TITLE,
        )

    img = img.resize((width // scale, height // scale), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def build_empty_series(days: int, end: date) -> list[dict]:
    start = end - timedelta(days=days - 1)
    out: list[dict] = []
    cur = start
    while cur <= end:
        out.append(
            {
                "day": cur,
                "parts": {t: 0 for t in CORE_HABIT_ORDER},
                "total": 0,
                "is_rest": False,
            }
        )
        cur += timedelta(days=1)
    return out
