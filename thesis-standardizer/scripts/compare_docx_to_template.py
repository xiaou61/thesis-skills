#!/usr/bin/env python3
"""Compare a thesis .docx against an extracted school template profile."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from extract_docx_template_profile import build_profile


MARGIN_TOLERANCE_CM = 0.3
PAGE_TOLERANCE_CM = 0.5
INDENT_TOLERANCE_CM = 0.2
POINT_TOLERANCE_PT = 1.0


@dataclass
class Finding:
    severity: str
    location: str
    message: str


def normalize_text(value: str) -> str:
    return " ".join(value.split()).strip()


def first_text(items: list[dict[str, Any]]) -> str:
    texts = []
    for item in items:
        if not isinstance(item, dict):
            continue
        texts.extend(item.get("text", []))
    return normalize_text(" ".join(texts))


def compare_number(
    findings: list[Finding],
    label: str,
    expected: float | None,
    actual: float | None,
    tolerance: float,
    location: str,
    severity: str = "major",
) -> None:
    if expected is None or actual is None:
        return
    if abs(expected - actual) > tolerance:
        findings.append(
            Finding(
                severity,
                location,
                f"{label} differs: expected {expected}cm, actual {actual}cm",
            )
        )


def compare_scalar(
    findings: list[Finding],
    location: str,
    label: str,
    expected: Any,
    actual: Any,
    severity: str = "major",
) -> None:
    if expected in (None, "", []):
        return
    if actual != expected:
        findings.append(
            Finding(
                severity,
                location,
                f"{label} differs: expected {expected}, actual {actual}",
            )
        )
    return


def compare_sections(template: dict[str, Any], thesis: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    template_sections = template.get("sections", [])
    thesis_sections = thesis.get("sections", [])

    if len(template_sections) != len(thesis_sections):
        findings.append(
            Finding(
                "major",
                "document",
                f"Section count differs: template has {len(template_sections)}, thesis has {len(thesis_sections)}",
            )
        )

    for idx, expected_section in enumerate(template_sections, 1):
        if idx > len(thesis_sections):
            break
        actual_section = thesis_sections[idx - 1]
        location = f"section {idx}"
        expected_page = expected_section.get("page", {})
        actual_page = actual_section.get("page", {})
        expected_page_number = expected_section.get("page_number", {}) or {}
        actual_page_number = actual_section.get("page_number", {}) or {}
        expected_first_page = bool(expected_section.get("different_first_page"))
        actual_first_page = bool(actual_section.get("different_first_page"))
        if expected_page.get("orientation") != actual_page.get("orientation"):
            findings.append(
                Finding(
                    "major",
                    location,
                    f"Orientation differs: expected {expected_page.get('orientation')}, actual {actual_page.get('orientation')}",
                )
            )
        if expected_first_page != actual_first_page:
            findings.append(
                Finding(
                    "major",
                    location,
                    "Different-first-page setting differs: "
                    f"expected {expected_first_page}, actual {actual_first_page}",
                )
            )
        compare_scalar(
            findings,
            location,
            "Page number start",
            expected_page_number.get("start"),
            actual_page_number.get("start"),
            "major",
        )
        compare_scalar(
            findings,
            location,
            "Page number format",
            expected_page_number.get("format"),
            actual_page_number.get("format"),
            "major",
        )
        compare_number(findings, "Page width", expected_page.get("width_cm"), actual_page.get("width_cm"), PAGE_TOLERANCE_CM, location)
        compare_number(findings, "Page height", expected_page.get("height_cm"), actual_page.get("height_cm"), PAGE_TOLERANCE_CM, location)

        for edge in ("top", "bottom", "left", "right"):
            compare_number(
                findings,
                f"Margin {edge}",
                expected_section.get("margins_cm", {}).get(edge),
                actual_section.get("margins_cm", {}).get(edge),
                MARGIN_TOLERANCE_CM,
                location,
            )

        expected_header = first_text(expected_section.get("headers", []))
        actual_header = first_text(actual_section.get("headers", []))
        expected_header_types = sorted(
            str(item.get("type", "default")) for item in expected_section.get("headers", []) if isinstance(item, dict)
        )
        actual_header_types = sorted(
            str(item.get("type", "default")) for item in actual_section.get("headers", []) if isinstance(item, dict)
        )
        if expected_header_types != actual_header_types:
            findings.append(
                Finding(
                    "major",
                    location,
                    f"Header type set differs: expected {expected_header_types}, actual {actual_header_types}",
                )
            )
        if expected_header and not actual_header:
            findings.append(
                Finding(
                    "major",
                    location,
                    f"Header preview missing: expected '{expected_header}', actual is empty",
                )
            )
        elif not expected_header and actual_header:
            findings.append(
                Finding(
                    "minor",
                    location,
                    f"Header preview unexpected: template is empty, actual '{actual_header}'",
                )
            )
        elif expected_header and actual_header and expected_header != actual_header:
            findings.append(
                Finding(
                    "minor",
                    location,
                    f"Header preview differs: expected '{expected_header}', actual '{actual_header}'",
                )
            )

        expected_footer = first_text(expected_section.get("footers", []))
        actual_footer = first_text(actual_section.get("footers", []))
        expected_footer_types = sorted(
            str(item.get("type", "default")) for item in expected_section.get("footers", []) if isinstance(item, dict)
        )
        actual_footer_types = sorted(
            str(item.get("type", "default")) for item in actual_section.get("footers", []) if isinstance(item, dict)
        )
        if expected_footer_types != actual_footer_types:
            findings.append(
                Finding(
                    "major",
                    location,
                    f"Footer type set differs: expected {expected_footer_types}, actual {actual_footer_types}",
                )
            )
        if expected_footer and not actual_footer:
            findings.append(
                Finding(
                    "major",
                    location,
                    f"Footer preview missing: expected '{expected_footer}', actual is empty",
                )
            )
        elif not expected_footer and actual_footer:
            findings.append(
                Finding(
                    "minor",
                    location,
                    f"Footer preview unexpected: template is empty, actual '{actual_footer}'",
                )
            )
        elif expected_footer and actual_footer and expected_footer != actual_footer:
            findings.append(
                Finding(
                    "minor",
                    location,
                    f"Footer preview differs: expected '{expected_footer}', actual '{actual_footer}'",
                )
            )

    return findings


def build_style_count_map(profile: dict[str, Any]) -> dict[str, int]:
    return {
        item.get("style_id", ""): int(item.get("count", 0))
        for item in profile.get("paragraph_usage", {}).get("style_counts", [])
        if isinstance(item, dict) and item.get("style_id")
    }


def build_style_map(profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item.get("style_id", ""): item
        for item in profile.get("styles", [])
        if isinstance(item, dict) and item.get("style_id")
    }


def build_style_sample_map(profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item.get("style_id", ""): item
        for item in profile.get("paragraph_usage", {}).get("style_format_samples", [])
        if isinstance(item, dict) and item.get("style_id")
    }


def ordered_samples(profile: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in profile.get("paragraph_usage", {}).get("ordered_paragraph_samples", [])
        if isinstance(item, dict)
    ]


def compare_heading_styles(template: dict[str, Any], thesis: dict[str, Any], overrides: dict[str, Any] | None) -> list[Finding]:
    findings: list[Finding] = []
    thesis_counts = build_style_count_map(thesis)
    template_counts = build_style_count_map(template)
    mapping = []
    if overrides:
        mapping = overrides.get("template_rule_overrides", {}).get("heading_style_map", []) or []

    for item in mapping:
        if not isinstance(item, dict):
            continue
        style_id = str(item.get("style_id", "")).strip()
        likely_level = str(item.get("likely_level", "")).strip()
        if not style_id:
            continue
        if style_id not in thesis_counts:
            findings.append(
                Finding(
                    "major" if "chapter" in likely_level or "heading_level_1" in likely_level else "minor",
                    "heading styles",
                    f"Expected heading style '{style_id}' ({likely_level}) is not used in thesis document",
                )
            )

    for style_id, count in thesis_counts.items():
        if style_id.startswith("Heading") and style_id not in template_counts:
            findings.append(
                Finding(
                    "minor",
                    "heading styles",
                    f"Thesis uses heading style '{style_id}' {count} time(s), but it was not seen in template samples",
                )
            )
    return findings


def compare_style_property(
    findings: list[Finding],
    location: str,
    label: str,
    expected: float | None,
    actual: float | None,
    tolerance: float,
    severity: str = "major",
) -> None:
    if expected is None:
        return
    if actual is None:
        findings.append(Finding(severity, location, f"{label} missing: expected {expected}, actual is empty"))
        return
    if abs(expected - actual) > tolerance:
        findings.append(Finding(severity, location, f"{label} differs: expected {expected}, actual {actual}"))


def compare_style_formats(template: dict[str, Any], thesis: dict[str, Any], overrides: dict[str, Any] | None) -> list[Finding]:
    findings: list[Finding] = []
    template_styles = build_style_map(template)
    thesis_styles = build_style_map(thesis)
    thesis_samples = build_style_sample_map(thesis)

    override_root = overrides.get("template_rule_overrides", {}) if isinstance(overrides, dict) else {}
    heading_items = override_root.get("heading_style_map", []) or []
    body_items = override_root.get("body_style_candidates", []) or []
    reference_items = override_root.get("reference_style_candidates", []) or []
    caption_items = override_root.get("caption_style_candidates", []) or []

    style_targets: list[tuple[str, dict[str, Any], str]] = []
    for item in heading_items:
        if isinstance(item, dict) and item.get("style_id"):
            style_targets.append((str(item["style_id"]), item, "heading"))
    for item in body_items:
        if isinstance(item, dict) and item.get("style_id"):
            style_targets.append((str(item["style_id"]), item, "body"))
    for item in reference_items:
        if isinstance(item, dict) and item.get("style_id"):
            style_targets.append((str(item["style_id"]), item, "reference"))
    for item in caption_items:
        if isinstance(item, dict) and item.get("style_id"):
            style_targets.append((str(item["style_id"]), item, "caption"))

    seen: set[str] = set()
    for style_id, override_item, bucket in style_targets:
        if style_id in seen:
            continue
        seen.add(style_id)
        template_style = template_styles.get(style_id)
        thesis_style = thesis_styles.get(style_id)
        sample = thesis_samples.get(style_id, {})
        style_name = str((template_style or thesis_style or override_item).get("style_name") or (template_style or thesis_style or {}).get("name") or style_id)
        location = f"style {style_name} ({style_id})"

        if template_style is None:
            continue
        if thesis_style is None:
            findings.append(Finding("major" if bucket == "heading" else "minor", location, "Style definition missing in thesis document"))
            continue

        expected_font = template_style.get("font_east_asia") or template_style.get("font_ascii")
        actual_font = thesis_style.get("font_east_asia") or thesis_style.get("font_ascii")
        base_severity = "major" if bucket == "heading" else "minor"
        compare_scalar(findings, location, "Font family", expected_font, actual_font, base_severity)
        compare_style_property(findings, location, "Font size pt", template_style.get("font_size_pt"), thesis_style.get("font_size_pt"), POINT_TOLERANCE_PT, base_severity)
        compare_scalar(findings, location, "Bold", template_style.get("bold"), thesis_style.get("bold"), "minor")
        compare_scalar(findings, location, "Italic", template_style.get("italic"), thesis_style.get("italic"), "minor")
        compare_scalar(findings, location, "Alignment", template_style.get("alignment"), thesis_style.get("alignment"), base_severity)
        compare_style_property(findings, location, "Spacing before pt", template_style.get("spacing_before_pt"), thesis_style.get("spacing_before_pt"), POINT_TOLERANCE_PT, "minor")
        compare_style_property(findings, location, "Spacing after pt", template_style.get("spacing_after_pt"), thesis_style.get("spacing_after_pt"), POINT_TOLERANCE_PT, "minor")
        compare_style_property(findings, location, "Line spacing pt", template_style.get("line_spacing_pt"), thesis_style.get("line_spacing_pt"), POINT_TOLERANCE_PT, "minor")
        compare_scalar(findings, location, "Line spacing rule", template_style.get("line_spacing_rule"), thesis_style.get("line_spacing_rule"), "minor")
        compare_style_property(findings, location, "First-line indent cm", template_style.get("first_line_indent_cm"), thesis_style.get("first_line_indent_cm"), INDENT_TOLERANCE_CM, "minor")
        compare_style_property(findings, location, "Left indent cm", template_style.get("left_indent_cm"), thesis_style.get("left_indent_cm"), INDENT_TOLERANCE_CM, "minor")
        compare_style_property(findings, location, "Hanging indent cm", template_style.get("hanging_indent_cm"), thesis_style.get("hanging_indent_cm"), INDENT_TOLERANCE_CM, "minor")

        sample_props = sample.get("paragraph_properties", {}) if isinstance(sample, dict) else {}
        if sample_props:
            if sample_props.get("alignment") is not None:
                compare_scalar(
                    findings,
                    f"{location} sample",
                    "Paragraph alignment sample",
                    template_style.get("alignment"),
                    sample_props.get("alignment"),
                    "minor",
                )
            if sample_props.get("first_line_indent_cm") is not None:
                compare_style_property(
                    findings,
                    f"{location} sample",
                    "Paragraph first-line indent cm sample",
                    template_style.get("first_line_indent_cm"),
                    sample_props.get("first_line_indent_cm"),
                    INDENT_TOLERANCE_CM,
                    "minor",
                )
            if sample_props.get("spacing_after_pt") is not None:
                compare_style_property(
                    findings,
                    f"{location} sample",
                    "Paragraph spacing after pt sample",
                    template_style.get("spacing_after_pt"),
                    sample_props.get("spacing_after_pt"),
                    POINT_TOLERANCE_PT,
                    "minor",
                )
            if sample_props.get("line_spacing_pt") is not None:
                compare_style_property(
                    findings,
                    f"{location} sample",
                    "Paragraph line spacing pt sample",
                    template_style.get("line_spacing_pt"),
                    sample_props.get("line_spacing_pt"),
                    POINT_TOLERANCE_PT,
                    "minor",
                )
    return findings


def detect_caption_position(ordered: list[dict[str, Any]], prefix: str) -> str:
    candidates: list[str] = []
    for idx, item in enumerate(ordered):
        text = str(item.get("text", "")).strip()
        style_name = str(item.get("style_name", "")).lower()
        if not text:
            continue
        if not (text.startswith(prefix) or text.lower().startswith("figure" if prefix == "图" else "table") or "caption" in style_name):
            continue
        prev_style = str(ordered[idx - 1].get("style_name", "")).lower() if idx > 0 else ""
        next_style = str(ordered[idx + 1].get("style_name", "")).lower() if idx + 1 < len(ordered) else ""
        prev_is_caption = "caption" in prev_style
        next_is_caption = "caption" in next_style
        if prefix == "图":
            if idx > 0 and not prev_is_caption:
                candidates.append("below")
            elif idx + 1 < len(ordered) and not next_is_caption:
                candidates.append("above")
        else:
            if idx + 1 < len(ordered) and not next_is_caption:
                candidates.append("above")
            elif idx > 0 and not prev_is_caption:
                candidates.append("below")
    if not candidates:
        return "unknown"
    return max(set(candidates), key=candidates.count)


def compare_caption_positions(thesis: dict[str, Any], overrides: dict[str, Any] | None) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(overrides, dict):
        return findings
    rules = overrides.get("template_rule_overrides", {}).get("caption_position_rules", {}) or {}
    thesis_order = ordered_samples(thesis)
    expected_figure = str(rules.get("figure_caption_position", "unknown"))
    expected_table = str(rules.get("table_caption_position", "unknown"))
    if expected_figure != "unknown":
        actual_figure = detect_caption_position(thesis_order, "图")
        if actual_figure != "unknown" and actual_figure != expected_figure:
            findings.append(Finding("minor", "caption position", f"Figure caption position differs: expected {expected_figure}, actual {actual_figure}"))
    if expected_table != "unknown":
        actual_table = detect_caption_position(thesis_order, "表")
        if actual_table != "unknown" and actual_table != expected_table:
            findings.append(Finding("minor", "caption position", f"Table caption position differs: expected {expected_table}, actual {actual_table}"))
    return findings


def detect_first_page_number_section(profile: dict[str, Any]) -> int | None:
    sections = profile.get("sections", []) or []
    for item in sections:
        if not isinstance(item, dict):
            continue
        page_number = item.get("page_number", {}) or {}
        if page_number.get("start") is not None or page_number.get("format") is not None:
            index = item.get("index")
            return int(index) if index is not None else None
    return None


def detect_first_body_page_number_section(profile: dict[str, Any], body_start_section_index: int | None) -> int | None:
    if body_start_section_index is None:
        return detect_first_page_number_section(profile)
    for item in detect_explicit_page_number_sections(profile):
        if int(item.get("index", 0) or 0) >= int(body_start_section_index):
            return int(item["index"])
    return None


def detect_explicit_page_number_sections(profile: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for item in profile.get("sections", []) or []:
        if not isinstance(item, dict):
            continue
        page_number = item.get("page_number", {}) or {}
        start = page_number.get("start")
        fmt = page_number.get("format")
        if start is None and fmt is None:
            continue
        index = item.get("index")
        if index is None:
            continue
        events.append(
            {
                "index": int(index),
                "start": start,
                "format": fmt,
            }
        )
    return events


def detect_first_explicit_page_number_section_at_or_after(profile: dict[str, Any], start_index: int | None) -> dict[str, Any] | None:
    if start_index is None:
        return None
    for item in detect_explicit_page_number_sections(profile):
        if int(item.get("index", 0) or 0) >= int(start_index):
            return item
    return None


def detect_role_section_indices(profile: dict[str, Any], role_name: str) -> list[int]:
    ordered = ordered_samples(profile)
    indices: set[int] = set()
    for item in ordered:
        section_index = int(item.get("section_index", 0) or 0)
        text = str(item.get("text", "")).strip().lower().replace(" ", "")
        if section_index <= 0 or not text:
            continue
        if role_name == "table_of_contents" and ("目录" in text or "contents" in text):
            indices.add(section_index)
        if role_name == "back_matter" and any(token in text for token in ("参考文献", "附录", "appendix", "致谢")):
            indices.add(section_index)
    return sorted(indices)


def compare_section_roles_and_page_number_start(thesis: dict[str, Any], overrides: dict[str, Any] | None) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(overrides, dict):
        return findings
    root = overrides.get("template_rule_overrides", {}) or {}
    expected_body_start = root.get("body_start_section_index")
    actual_page_number_section = detect_first_body_page_number_section(
        thesis,
        int(expected_body_start) if expected_body_start not in (None, "", 0) else None,
    )
    if expected_body_start is not None and actual_page_number_section is not None and int(expected_body_start) != int(actual_page_number_section):
        findings.append(
            Finding(
                "major",
                "section roles",
                f"First explicit body page-number section differs from expected body-start section: expected section {expected_body_start}, actual section {actual_page_number_section}",
            )
        )
    return findings


def compare_front_matter_page_number_rules(thesis: dict[str, Any], overrides: dict[str, Any] | None) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(overrides, dict):
        return findings
    root = overrides.get("template_rule_overrides", {}) or {}
    expected_body_start = root.get("body_start_section_index")
    if expected_body_start in (None, "", 0):
        return findings

    template_front_section_rules = {
        int(item.get("section_index", 0) or 0): item
        for item in root.get("section_header_footer_rules", []) or []
        if isinstance(item, dict) and int(item.get("section_index", 0) or 0) < int(expected_body_start)
    }

    for section in thesis.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        index = int(section.get("index", 0) or 0)
        if index <= 0 or index >= int(expected_body_start):
            continue
        page_number = section.get("page_number", {}) or {}
        start = page_number.get("start")
        fmt = page_number.get("format")
        expected_rule = template_front_section_rules.get(index, {})
        expected_start = expected_rule.get("page_number_start")
        expected_format = expected_rule.get("page_number_format")
        if (start is not None or fmt is not None) and expected_start is None and expected_format is None:
            findings.append(
                Finding(
                    "major",
                    f"section {index}",
                    "Front-matter section has explicit page-number settings before expected body-start section",
                )
            )
    return findings


def compare_page_number_format_zones(
    template: dict[str, Any],
    thesis: dict[str, Any],
    overrides: dict[str, Any] | None,
) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(overrides, dict):
        return findings
    root = overrides.get("template_rule_overrides", {}) or {}
    expected_body_start = root.get("body_start_section_index")
    if expected_body_start in (None, "", 0):
        return findings

    expected_body_start = int(expected_body_start)
    template_front_formats = {
        str(item.get("format"))
        for item in detect_explicit_page_number_sections(template)
        if int(item.get("index", 0) or 0) < expected_body_start and item.get("format") not in (None, "")
    }
    thesis_front_formats = {
        str(item.get("format"))
        for item in detect_explicit_page_number_sections(thesis)
        if int(item.get("index", 0) or 0) < expected_body_start and item.get("format") not in (None, "")
    }

    roman_formats = {"roman", "upperRoman", "lowerRoman"}
    decimal_formats = {"decimal"}
    if template_front_formats & roman_formats and thesis_front_formats & decimal_formats:
        findings.append(
            Finding(
                "major",
                "page-number zones",
                "Front-matter page-number format appears to switch to Arabic numerals before body start, while template front matter uses Roman numerals",
            )
        )
    if template_front_formats and thesis_front_formats and template_front_formats != thesis_front_formats:
        findings.append(
            Finding(
                "major",
                "page-number zones",
                f"Front-matter explicit page-number formats differ: expected {sorted(template_front_formats)}, actual {sorted(thesis_front_formats)}",
            )
        )

    template_body_event = next(
        (item for item in detect_explicit_page_number_sections(template) if int(item.get("index", 0) or 0) == expected_body_start),
        None,
    )
    thesis_body_event = next(
        (item for item in detect_explicit_page_number_sections(thesis) if int(item.get("index", 0) or 0) == expected_body_start),
        None,
    )
    if template_body_event and thesis_body_event:
        expected_fmt = template_body_event.get("format")
        actual_fmt = thesis_body_event.get("format")
        if expected_fmt and actual_fmt and expected_fmt != actual_fmt:
            findings.append(
                Finding(
                    "major",
                    f"section {expected_body_start}",
                    f"Body-start page-number format differs: expected {expected_fmt}, actual {actual_fmt}",
                )
            )
    return findings


def compare_unexpected_page_number_restarts(
    template: dict[str, Any],
    thesis: dict[str, Any],
    overrides: dict[str, Any] | None,
) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(overrides, dict):
        return findings
    root = overrides.get("template_rule_overrides", {}) or {}
    expected_body_start = root.get("body_start_section_index")
    if expected_body_start in (None, "", 0):
        return findings

    template_sections = {
        int(item.get("index", 0) or 0): item
        for item in template.get("sections", []) or []
        if isinstance(item, dict) and int(item.get("index", 0) or 0) > 0
    }
    for section in thesis.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        index = int(section.get("index", 0) or 0)
        if index <= int(expected_body_start):
            continue
        actual_page_number = section.get("page_number", {}) or {}
        actual_start = actual_page_number.get("start")
        actual_format = actual_page_number.get("format")
        expected_section = template_sections.get(index, {})
        expected_page_number = expected_section.get("page_number", {}) or {}
        expected_start = expected_page_number.get("start")
        expected_format = expected_page_number.get("format")
        if actual_start is not None and expected_start is None:
            findings.append(
                Finding(
                    "major",
                    f"section {index}",
                    f"Unexpected explicit page-number restart detected after body start: template has no restart here, actual start is {actual_start}",
                )
            )
        if actual_format is not None and expected_format is None and expected_start is None:
            findings.append(
                Finding(
                    "minor",
                    f"section {index}",
                    f"Unexpected explicit page-number format override detected after body start: template has no explicit format here, actual format is {actual_format}",
                )
            )
    return findings


def compare_page_number_event_continuity(
    template: dict[str, Any],
    thesis: dict[str, Any],
    overrides: dict[str, Any] | None,
) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(overrides, dict):
        return findings
    root = overrides.get("template_rule_overrides", {}) or {}
    expected_body_start = root.get("body_start_section_index")
    if expected_body_start in (None, "", 0):
        return findings

    expected_body_start = int(expected_body_start)
    template_events = [
        item for item in detect_explicit_page_number_sections(template) if int(item.get("index", 0) or 0) >= expected_body_start
    ]
    thesis_events = [
        item for item in detect_explicit_page_number_sections(thesis) if int(item.get("index", 0) or 0) >= expected_body_start
    ]
    template_indices = [int(item["index"]) for item in template_events]
    thesis_indices = [int(item["index"]) for item in thesis_events]
    if template_indices != thesis_indices:
        findings.append(
            Finding(
                "major",
                "page-number continuity",
                f"Explicit page-number section sequence differs after body start: expected {template_indices}, actual {thesis_indices}",
            )
        )
        return findings

    for expected_event, actual_event in zip(template_events, thesis_events):
        expected_start = expected_event.get("start")
        actual_start = actual_event.get("start")
        expected_format = expected_event.get("format")
        actual_format = actual_event.get("format")
        index = int(expected_event["index"])
        if expected_start != actual_start:
            findings.append(
                Finding(
                    "major",
                    f"section {index}",
                    f"Explicit page-number restart value differs from template sequence: expected {expected_start}, actual {actual_start}",
                )
            )
        if expected_format != actual_format:
            findings.append(
                Finding(
                    "major",
                    f"section {index}",
                    f"Explicit page-number restart format differs from template sequence: expected {expected_format}, actual {actual_format}",
                )
            )
    return findings


def compare_back_matter_page_number_policy(
    template: dict[str, Any],
    thesis: dict[str, Any],
    overrides: dict[str, Any] | None,
) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(overrides, dict):
        return findings
    root = overrides.get("template_rule_overrides", {}) or {}
    back_matter_start = root.get("back_matter_start_section_index")
    if back_matter_start in (None, "", 0):
        return findings

    back_matter_start = int(back_matter_start)
    template_event = detect_first_explicit_page_number_section_at_or_after(template, back_matter_start)
    thesis_event = detect_first_explicit_page_number_section_at_or_after(thesis, back_matter_start)

    if template_event is None and thesis_event is not None:
        findings.append(
            Finding(
                "major",
                "back matter",
                f"Back-matter page numbering unexpectedly restarts at section {thesis_event['index']}; template back matter appears to continue existing numbering",
            )
        )
        return findings

    if template_event is not None and thesis_event is None:
        findings.append(
            Finding(
                "major",
                "back matter",
                f"Back-matter page numbering restart is missing: template restarts or formats numbering from section {template_event['index']}",
            )
        )
        return findings

    if template_event is None or thesis_event is None:
        return findings

    if int(template_event["index"]) != int(thesis_event["index"]):
        findings.append(
            Finding(
                "major",
                "back matter",
                f"Back-matter page-number restart section differs: expected section {template_event['index']}, actual section {thesis_event['index']}",
            )
        )
    if template_event.get("start") != thesis_event.get("start"):
        findings.append(
            Finding(
                "major",
                "back matter",
                f"Back-matter page-number restart value differs: expected {template_event.get('start')}, actual {thesis_event.get('start')}",
            )
        )
    if template_event.get("format") != thesis_event.get("format"):
        findings.append(
            Finding(
                "major",
                "back matter",
                f"Back-matter page-number format differs: expected {template_event.get('format')}, actual {thesis_event.get('format')}",
            )
        )
    return findings


def compare_toc_boundary_policy(thesis: dict[str, Any], overrides: dict[str, Any] | None) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(overrides, dict):
        return findings
    root = overrides.get("template_rule_overrides", {}) or {}
    toc_indices = [int(x) for x in (root.get("toc_section_indices") or []) if int(x or 0) > 0]
    expected_body_start = root.get("body_start_section_index")
    if not toc_indices or expected_body_start in (None, "", 0):
        return findings

    expected_body_start = int(expected_body_start)
    expected_after_toc = max(toc_indices) + 1
    if expected_after_toc != expected_body_start:
        findings.append(
            Finding(
                "major",
                "table of contents",
                f"Template TOC boundary and body-start boundary are inconsistent: last TOC section implies body should start at section {expected_after_toc}, but extracted body-start section is {expected_body_start}",
            )
        )
        return findings

    actual_toc_indices = detect_role_section_indices(thesis, "table_of_contents")
    if actual_toc_indices:
        actual_after_toc = max(actual_toc_indices) + 1
        if actual_after_toc != expected_after_toc:
            findings.append(
                Finding(
                    "major",
                    "table of contents",
                    f"TOC boundary differs from template: expected body to start after TOC at section {expected_after_toc}, actual TOC boundary implies section {actual_after_toc}",
                )
            )
    return findings


def render_markdown(thesis_docx: Path, template_json: Path, findings: list[Finding]) -> str:
    lines = [
        "# DOCX Template Comparison Report",
        "",
        f"- Thesis document: `{thesis_docx}`",
        f"- Template profile: `{template_json}`",
        f"- Finding count: `{len(findings)}`",
        "",
    ]
    if not findings:
        lines.append("- No structural differences detected within current comparison scope.")
        return "\n".join(lines) + "\n"

    grouped = {"critical": [], "major": [], "minor": []}
    for finding in findings:
        grouped.setdefault(finding.severity, []).append(finding)

    for severity in ("critical", "major", "minor"):
        bucket = grouped.get(severity) or []
        if not bucket:
            continue
        lines.extend([f"## {severity.title()} Findings", ""])
        for item in bucket:
            lines.append(f"- `{item.location}`: {item.message}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare a thesis docx against an extracted template profile.")
    parser.add_argument("thesis_docx", help="Final or draft thesis .docx to inspect.")
    parser.add_argument("template_profile_json", help="template-profile.json path extracted from school template.")
    parser.add_argument("--template-rule-overrides", help="Optional template-rule-overrides.yaml path.")
    parser.add_argument("--out", default="paper-context/template-compare/template-compare-report.md", help="Output markdown report path.")
    parser.add_argument("--json-out", help="Optional JSON report path.")
    args = parser.parse_args()

    thesis_docx = Path(args.thesis_docx).resolve()
    template_json = Path(args.template_profile_json).resolve()
    thesis_profile = build_profile(thesis_docx)
    template_profile = json.loads(template_json.read_text(encoding="utf-8"))

    overrides = None
    if args.template_rule_overrides:
        import yaml  # local import to keep dependency optional outside this path

        overrides = yaml.safe_load(Path(args.template_rule_overrides).resolve().read_text(encoding="utf-8"))

    findings = []
    findings.extend(compare_sections(template_profile, thesis_profile))
    findings.extend(compare_heading_styles(template_profile, thesis_profile, overrides))
    findings.extend(compare_style_formats(template_profile, thesis_profile, overrides))
    findings.extend(compare_caption_positions(thesis_profile, overrides))
    findings.extend(compare_section_roles_and_page_number_start(thesis_profile, overrides))
    findings.extend(compare_front_matter_page_number_rules(thesis_profile, overrides))
    findings.extend(compare_page_number_format_zones(template_profile, thesis_profile, overrides))
    findings.extend(compare_unexpected_page_number_restarts(template_profile, thesis_profile, overrides))
    findings.extend(compare_page_number_event_continuity(template_profile, thesis_profile, overrides))
    findings.extend(compare_back_matter_page_number_policy(template_profile, thesis_profile, overrides))
    findings.extend(compare_toc_boundary_policy(thesis_profile, overrides))

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_markdown(thesis_docx, template_json, findings), encoding="utf-8")
    print(f"Wrote {out_path}")

    if args.json_out:
        json_path = Path(args.json_out).resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "thesis_docx": str(thesis_docx),
            "template_profile_json": str(template_json),
            "finding_count": len(findings),
            "findings": [finding.__dict__ for finding in findings],
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {json_path}")

    return 0 if not any(item.severity in {"critical", "major"} for item in findings) else 2


if __name__ == "__main__":
    raise SystemExit(main())
