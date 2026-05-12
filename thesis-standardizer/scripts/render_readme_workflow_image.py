#!/usr/bin/env python3
"""Render the README thesis workflow as a PNG image."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "readme" / "thesis-workflow.png"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, fnt: ImageFont.ImageFont) -> list[str]:
    lines: list[str] = []
    for raw_line in text.split("\n"):
        line = ""
        for char in raw_line:
            test = line + char
            if draw.textbbox((0, 0), test, font=fnt)[2] <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = char
        if line:
            lines.append(line)
    return lines


def rounded_box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    fill: str,
    outline: str,
    title: str,
    body: str,
    accent: str,
) -> None:
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=24, fill=fill, outline=outline, width=3)
    draw.rounded_rectangle((x1, y1, x2, y1 + 16), radius=8, fill=accent)
    title_font = font(28, bold=True)
    body_font = font(21)
    draw.text((x1 + 28, y1 + 28), title, fill="#17202A", font=title_font)
    lines = wrap_text(draw, body, x2 - x1 - 56, body_font)
    y = y1 + 78
    for line in lines[:4]:
        draw.text((x1 + 28, y), line, fill="#34495E", font=body_font)
        y += 31


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = "#607D8B") -> None:
    draw.line((start, end), fill=color, width=5)
    ex, ey = end
    sx, sy = start
    if abs(ex - sx) >= abs(ey - sy):
        sign = 1 if ex > sx else -1
        points = [(ex, ey), (ex - sign * 18, ey - 11), (ex - sign * 18, ey + 11)]
    else:
        sign = 1 if ey > sy else -1
        points = [(ex, ey), (ex - 11, ey - sign * 18), (ex + 11, ey - sign * 18)]
    draw.polygon(points, fill=color)


def main() -> int:
    width, height = 1800, 1280
    img = Image.new("RGB", (width, height), "#F7F8FA")
    draw = ImageDraw.Draw(img)

    title_font = font(48, bold=True)
    sub_font = font(24)
    draw.text((70, 48), "论文编写一整套工作流", fill="#101820", font=title_font)
    draw.text((72, 116), "从材料整理到终稿交付，全程保留证据、AIGC 报告和修改追溯日志", fill="#536270", font=sub_font)

    boxes = [
        ((80, 190, 430, 360), "#EAF4FF", "#7DB4E6", "1. 准备材料", "学校模板、任务书、源码、截图、测试记录、已有文献", "#6AAFE6"),
        ((520, 190, 870, 360), "#EFF8F0", "#8BCB8F", "2. 初始化资料包", "建立标准、论文事实、证据清单、缺失材料和章节草案", "#7BC77E"),
        ((960, 190, 1310, 360), "#FFF6E6", "#E8B35D", "3. 证据检查", "证据不足就标记缺口，不硬写、不补造", "#E7A843"),
        ((1390, 190, 1740, 360), "#F2EEFF", "#A78BDB", "4. 文献路径", "自动查找文献，或手动指定关键词、文献清单和年份范围", "#9575CD"),
        ((1390, 500, 1740, 690), "#EAF7F7", "#69B7B2", "5. 目录与图表", "规划章节、图表编号、引用位置和证据来源", "#55AAA5"),
        ((960, 500, 1310, 690), "#FFF0F0", "#E08B8B", "6. 分章写作", "先列证据，再写正文；不补造功能、数据或引用", "#D97878"),
        ((520, 500, 870, 690), "#F3F6FF", "#849CE3", "7. AIGC 检测", "估计 AIGC 率、扫描维度、段落风险和修改优先级", "#7289DA"),
        ((80, 500, 430, 690), "#FFF7FA", "#DE89AC", "8. 风格治理", "只改高风险段落；保留事实、数据、引用和论文语体", "#D9709A"),
        ((80, 830, 430, 1030), "#F5F5F5", "#AAB2BD", "9. 逐段终稿", "需要时逐段降低 AIGC；极度消耗 token，逐段记录", "#8F9AA6"),
        ((520, 830, 870, 1030), "#EEF8FF", "#71B7D4", "10. 修改追溯", "记录改了哪里、为什么改、依据是什么、涉及哪些文件", "#5FA7C7"),
        ((960, 830, 1310, 1030), "#F0FFF4", "#75BD85", "11. 终稿检查", "检查学校格式、证据链、引用闭环、图表和 Word/PDF 风险", "#66AC75"),
        ((1390, 830, 1740, 1030), "#FFF3E8", "#E0A06A", "12. 交付归档", "交付论文终稿，同时保留报告、日志和证据包", "#D58D52"),
    ]

    for box in boxes:
        rounded_box(draw, *box)

    arrows = [
        ((430, 275), (520, 275)),
        ((870, 275), (960, 275)),
        ((1310, 275), (1390, 275)),
        ((1565, 360), (1565, 500)),
        ((1390, 595), (1310, 595)),
        ((960, 595), (870, 595)),
        ((520, 595), (430, 595)),
        ((255, 690), (255, 830)),
        ((430, 930), (520, 930)),
        ((870, 930), (960, 930)),
        ((1310, 930), (1390, 930)),
    ]
    for start, end in arrows:
        arrow(draw, start, end)

    note_font = font(20)
    draw.rounded_rectangle((80, 1110, 1740, 1190), radius=20, fill="#FFFFFF", outline="#D5DAE0", width=2)
    draw.text(
        (110, 1132),
        "核心原则：学校模板优先；文献真实可核验；AIGC 检测只是本地估计；所有实质性修改都要写入追溯日志。",
        fill="#34495E",
        font=note_font,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, quality=95)
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
