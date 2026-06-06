#!/usr/bin/env python3
"""Apply visible thesis variant emphasis to a generated DOCX.

This script intentionally makes conservative body-text edits only. It does not
touch relationships, media, embedded Visio objects, styles, or numbering parts.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


PARAGRAPH_RE = re.compile(r"(<w:p\b[^>]*>.*?</w:p>)", re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class Insertion:
    anchor: str
    position: str
    paragraphs: list[str]


PROFILES: dict[str, list[Insertion]] = {
    "template_first": [
        Insertion(
            "第4章　系统设计",
            "before",
            [
                "本章承接前文需求分析内容，从功能结构、系统架构、部署结构和数据结构四个层面展开设计。章节安排遵循先总体后局部、先业务后数据的顺序，使后续实现章节能够直接对应设计结果。",
            ],
        ),
        Insertion(
            "第5章　系统实现",
            "before",
            [
                "在完成系统设计后，本文进一步说明关键模块的实现方法。实现章节按照登录认证、请假审批、活动报名和界面运行效果展开，避免将测试内容提前放入实现章节。",
            ],
        ),
        Insertion(
            "第6章　系统测试",
            "before",
            [
                "系统测试章节在实现章节之后展开，重点检查主要业务流程是否能够按照设计目标运行。测试内容以环境、用例和结果为主，保持与系统实现章节的边界清晰。",
            ],
        ),
    ],
    "figure_enhanced": [
        Insertion(
            "系统用例图如图 3.1 所示",
            "after",
            [
                "从系统用例图可以看出，系统并没有把所有操作集中在单一角色中，而是围绕管理员、教师和学生形成较明确的职责边界。这样的划分有助于后续权限控制和接口访问控制的实现。",
            ],
        ),
        Insertion(
            "系统总体架构如图 4.2 所示",
            "after",
            [
                "从系统总体架构图可以看出，前端访问层、后端服务层和数据存储层之间保持清晰协作关系。该结构使业务处理逻辑集中在后端服务中，前端主要负责交互展示，数据库负责持久化保存。",
            ],
        ),
        Insertion(
            "系统总体E-R图如图 4.4 所示",
            "after",
            [
                "系统总体 E-R 图重点表达实体之间的业务联系，用户实体通过不同关系连接请假、报修、公告、活动和活动报名等对象。为避免总体图过度拥挤，字段细节在后续单实体 E-R 图和数据表中展开。",
            ],
        ),
        Insertion(
            "JWT登录认证实现流程如图 5.1 所示",
            "after",
            [
                "JWT 登录认证流程将登录过程拆分为参数校验、用户查询、密码校验、令牌生成和结果返回几个步骤，能够更直观地说明登录接口与认证工具类之间的配合方式。",
            ],
        ),
        Insertion(
            "活动报名实现流程如图 5.3 所示",
            "after",
            [
                "活动报名实现流程体现了该模块的多重约束，系统需要依次检查用户角色、活动状态、重复报名和人数限制，随后再写入报名记录并更新活动报名人数。",
            ],
        ),
    ],
    "narrative_enhanced": [
        Insertion(
            "第4章　系统设计",
            "before",
            [
                "综上，需求分析章节明确了校园事务管理系统的角色范围、业务流程和功能边界。学生侧重发起申请和查看信息，教师侧重审批与发布，管理员侧重维护与监管，这一分析结果为系统设计提供了直接依据。",
            ],
        ),
        Insertion(
            "第5章　系统实现",
            "before",
            [
                "系统设计章节完成了从功能结构到数据结构的整体安排。实现阶段需要把这些设计结果落实到控制层、业务层、数据访问层和数据库表之间的协作中，从而形成可运行的后端服务。",
            ],
        ),
        Insertion(
            "第6章　系统测试",
            "before",
            [
                "系统实现章节说明了主要模块的实现过程，但实现完成并不意味着系统已经满足使用要求。因此，后续测试章节需要围绕登录认证、请假审批、报修处理、公告管理和活动报名等核心流程进行验证。",
            ],
        ),
        Insertion(
            "参考文献",
            "before",
            [
                "通过本系统的设计与实现，可以看出校园事务管理系统的价值不只体现在功能在线化，还体现在流程规范化和信息集中管理上。后续工作可继续补充前端交互细节、移动端适配和更完整的运行监控机制，以提升系统在实际校园场景中的使用效果。",
            ],
        ),
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path)
    parser.add_argument("--variant", required=True, choices=sorted(PROFILES))
    parser.add_argument("--out-report", type=Path)
    return parser.parse_args()


def paragraph_text(xml: str) -> str:
    return html.unescape(TAG_RE.sub("", xml)).strip()


def paragraph_xml(text: str) -> str:
    escaped = html.escape(text, quote=False)
    return (
        "<w:p>"
        "<w:pPr>"
        '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
        '<w:ind w:firstLineChars="200"/>'
        "</w:pPr>"
        "<w:r>"
        "<w:rPr><w:rFonts w:hint=\"eastAsia\"/></w:rPr>"
        f'<w:t xml:space="preserve">{escaped}</w:t>'
        "</w:r>"
        "</w:p>"
    )


def insert_into_document_xml(xml: str, insertions: list[Insertion]) -> tuple[str, list[dict[str, object]]]:
    paragraphs = list(PARAGRAPH_RE.finditer(xml))
    offset = 0
    actions: list[dict[str, object]] = []
    for insertion in insertions:
        added = 0
        if all(text in paragraph_text(xml) for text in insertion.paragraphs):
            actions.append({"anchor": insertion.anchor, "position": insertion.position, "inserted": 0, "reason": "already_present"})
            continue
        target = next((match for match in paragraphs if insertion.anchor in paragraph_text(match.group(0))), None)
        if target is None:
            actions.append({"anchor": insertion.anchor, "position": insertion.position, "inserted": 0, "reason": "anchor_not_found"})
            continue
        snippet = "".join(paragraph_xml(text) for text in insertion.paragraphs if text not in xml)
        if not snippet:
            actions.append({"anchor": insertion.anchor, "position": insertion.position, "inserted": 0, "reason": "already_present"})
            continue
        index = target.start() if insertion.position == "before" else target.end()
        index += offset
        xml = xml[:index] + snippet + xml[index:]
        offset += len(snippet)
        added = len(insertion.paragraphs)
        actions.append({"anchor": insertion.anchor, "position": insertion.position, "inserted": added, "reason": "ok"})
    return xml, actions


def update_docx(docx: Path, variant: str) -> dict[str, object]:
    docx = docx.resolve()
    if not docx.exists():
        raise FileNotFoundError(docx)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as handle:
        tmp = Path(handle.name)

    try:
        with ZipFile(docx, "r") as source, ZipFile(tmp, "w", ZIP_DEFLATED) as target:
            actions: list[dict[str, object]] = []
            for info in source.infolist():
                data = source.read(info.filename)
                if info.filename == "word/document.xml":
                    xml = data.decode("utf-8")
                    xml, actions = insert_into_document_xml(xml, PROFILES[variant])
                    data = xml.encode("utf-8")
                target.writestr(info, data)
        shutil.move(str(tmp), str(docx))
    finally:
        if tmp.exists():
            tmp.unlink()

    return {
        "docx": str(docx),
        "variant": variant,
        "insertions": actions,
        "inserted_paragraphs": sum(int(item["inserted"]) for item in actions),
    }


def main() -> int:
    args = parse_args()
    report = update_docx(args.docx, args.variant)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out_report:
        args.out_report.parent.mkdir(parents=True, exist_ok=True)
        args.out_report.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
