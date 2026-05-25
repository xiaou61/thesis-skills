# 本科系统类论文标准化套件

精简目标：基于一个真实程序，整理证据并生成本科系统类论文。

默认服务对象是软件系统、网站、小程序、管理系统、物联网平台等设计与实现类论文。其它论文类型可以借用模板，但不是当前主路径。

## 推荐使用顺序

1. 如果有学校 `.docx` 模板，先提取模板字号、页边距、样式、题注、三线表等格式事实。
2. 运行项目证据扫描，生成 `paper-context/evidence/`。
3. 填写三个核心文件：
   - `templates/standard-profile.yaml`
   - `templates/thesis-ai-spec.yaml`
   - `templates/figure-registry.yaml`
4. 按章节生成正文：
   - 第1章：绪论
   - 第2章：相关技术及其在本系统中的应用
   - 第3章：系统分析，用例图
   - 第4章：系统设计与实现，功能架构图、总E-R图、单实体E-R图、数据库三线表
   - 第5章：测试
   - 第6章：结论
5. 最后检查证据、图表、引用和 Word 格式风险。

## 文件结构

```text
thesis-ai-standard/
  README.md
  templates/
    standard-profile.yaml
    thesis-ai-spec.yaml
    figure-registry.yaml
    chapter-section-template.md
    ai-review-rubric.json
```

## 核心原则

- 不编造系统功能、实验数据、数据库字段、接口路径、测试结果和参考文献。
- 每张图、表、公式、截图都必须能追溯到正文位置和证据来源。
- 论文正文不得出现“根据用户提供材料”“通过分析代码”“让 AI 生成”等工作流痕迹。
- 学校模板和导师要求优先。

## 证据层建议

系统实现类项目建议建立：

```text
paper-context/
  evidence/
    project-evidence.json
    code-structure.md
    tech-stack.md
    api-list.md
    database-schema.md
    test-results.md
  workflow/
    revision-log.md
    revision-trace.jsonl
```

这些文件是论文事实依据，不是正文。AI 写作时必须把证据转化为论文语体，不能把扫描过程写进正文。
