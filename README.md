# docx-editor-cn

这个仓库现在使用 `Gostyan/docx-skill-4-cn-paper` 的 `docx-editor-cn` 作为主 skill，原来的 `thesis-standardizer` 论文标准化工作流已经被移除。

`docx-editor-cn` 面向中文学术 Word 文档排版，重点覆盖：

- Markdown 转 Word
- 中文论文 A4 页面与正文样式
- 标题层级与编号
- 图题、表题与三线表
- LaTeX 公式转 Word 原生公式
- 参考文献与上标引用
- 现有 `.docx` 解包、XML 编辑和重新打包

## Skill 目录

```text
docx-editor-cn/
├── SKILL.md
├── package.json
├── package-lock.json
├── scripts/
└── agents/openai.yaml
```

## 基本使用

进入 skill 目录安装依赖：

```bash
cd docx-editor-cn
npm install
```

生成模板文档：

```bash
node scripts/new_doc.js
```

编辑现有 Word 文档时，按 `docx-editor-cn/SKILL.md` 的流程执行：

```bash
python scripts/office/unpack.py input.docx unpacked/
python scripts/office/pack.py unpacked/ output.docx --original input.docx
```

## 来源

本 skill 来自：

https://github.com/Gostyan/docx-skill-4-cn-paper

