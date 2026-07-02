---
name: github-repo-publisher
version: "1.0.0"
description: "根据用户需求自动生成完整GitHub项目包（含README、docs、examples、pyproject.toml、skill.md等）并推送到指定仓库，支持后续迭代更新和自动更新CHANGELOG。适用于用户说'帮我做个项目并上传GitHub'、'生成一个GitHub包'、'帮我发布个项目'等场景。"
metadata:
  requires:
    bins: ["git"]
---

# GitHub 项目发布助手 (github-repo-publisher)

根据用户描述的需求，自动生成结构化的 GitHub 项目包（含完整文档、示例代码、配置文件），
并推送到指定仓库。支持后续迭代改进，自动更新 CHANGELOG 并重新推送。

## 定位

本 Skill 负责**从需求到 GitHub 仓库**的全流程：

- **新项目创建**：用户描述需求 → 生成完整项目结构 → 推送到 GitHub
- **后续迭代**：用户提出改进 → 修改代码 → 更新 CHANGELOG → 重新推送
- **项目包装**：确保项目符合 GitHub 开源项目最佳实践

## 触发场景

当用户出现以下意图时触发本 Skill：

- "帮我做个XX项目并上传到GitHub"
- "生成一个GitHub包"
- "帮我发布个项目"
- "把这个项目整理成GitHub仓库"
- "创建一个开源项目"
- "帮我推送到GitHub"
- "更新一下GitHub上的项目"
- "改进一下这个项目并重新推送"

## 工作模式

### 模式1：全新项目创建

当用户描述一个新项目需求时：

```
用户需求 → 分析拆解 → 生成代码 → 包装GitHub标准文件 → 推送
```

**标准文件清单**（每次新项目必须包含）：

| 文件 | 说明 | 必填 |
|------|------|------|
| `README.md` | 项目主页，含badge、功能、安装、使用、示例 | ✅ |
| `LICENSE` | 开源协议（默认MIT） | ✅ |
| `CHANGELOG.md` | 版本变更记录 | ✅ |
| `CONTRIBUTING.md` | 贡献指南 | ✅ |
| `.gitignore` | Git忽略规则 | ✅ |
| `.env.example` | 环境变量模板（如项目需要配置） | ⭕ |
| `pyproject.toml` / `package.json` | 包配置（根据语言选择） | ✅ |
| `requirements.txt` | 依赖清单（Python项目） | ⭕ |
| `skill.md` | Skill描述文件（如项目是Skill类型） | ⭕ |
| `docs/` | 文档目录（至少3篇：架构、使用、API） | ✅ |
| `examples/` | 示例代码（至少1个基础示例） | ✅ |

### 模式2：迭代更新

当用户对已有项目提出改进时：

```
用户改进需求 → 修改代码/文档 → 更新 CHANGELOG → 重新推送
```

**迭代流程规范**：

1. 先确认当前项目状态（`git status`、`git log --oneline -5`）
2. 修改对应代码/文档
3. 更新 `CHANGELOG.md`（在 `[Unreleased]` 或新增版本号下记录变更）
4. 提交（使用约定式提交格式：`feat: ...` / `fix: ...` / `docs: ...` 等）
5. 推送到远程仓库

### 模式3：纯推送

当用户已有代码，只需要推送到 GitHub 时：

1. 检查是否已初始化 Git 仓库
2. 检查 remote 配置
3. 如未初始化：`git init` → 初始提交 → 设置 remote → 推送
4. 如已初始化但未推送：直接推送

## 执行流程

### 第一步：需求澄清

在动手前，必须向用户确认以下信息（如果用户没有提供）：

| 信息 | 说明 | 默认值 |
|------|------|--------|
| 项目名称 | GitHub仓库名 | 从需求中推断 |
| 项目描述 | 一句话描述 | 从需求中推断 |
| 编程语言 | Python / JavaScript / 其他 | Python |
| GitHub 仓库 URL | 推送到哪里 | 需要用户提供 |
| 开源协议 | MIT / Apache / GPL 等 | MIT |

### 第二步：生成项目

按照以下顺序生成文件：

1. **核心代码**：先写功能代码
2. **示例代码**：`examples/basic_usage.py`（或对应语言）
3. **配置文件**：`pyproject.toml` / `package.json`
4. **文档**：
   - `README.md`（最后写，确保内容与实际代码一致）
   - `docs/ARCHITECTURE.md` — 架构设计
   - `docs/USAGE.md` — 使用指南
   - `docs/API.md` — API文档
5. **项目元文件**：
   - `LICENSE`（MIT）
   - `CHANGELOG.md`
   - `CONTRIBUTING.md`
   - `.gitignore`（对应语言的标准模板）
   - `.env.example`（如需要）
   - `skill.md`（如果项目本身是Skill类型）

### 第三步：Git 初始化与提交

```
git init
git branch -m main
git add .
git commit -m "feat: 项目 v1.0.0 初始版本"
```

提交信息遵循 **Conventional Commits** 规范：

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加用户登录功能` |
| `fix` | 修复bug | `fix: 修复登录页面闪退问题` |
| `docs` | 文档变更 | `docs: 更新README安装说明` |
| `style` | 代码格式（不影响功能） | `style: 调整缩进` |
| `refactor` | 重构 | `refactor: 重写认证模块` |
| `perf` | 性能优化 | `perf: 优化列表加载速度` |
| `test` | 测试相关 | `test: 添加单元测试` |
| `chore` | 构建/工具 | `chore: 更新依赖版本` |

### 第四步：获取仓库URL并推送

1. 询问用户 GitHub 仓库 URL
2. 如果用户还没创建仓库，引导用户：
   - 打开 GitHub → New repository
   - 填写仓库名
   - 选择 Public/Private
   - **不要**勾选 "Add a README"
   - 点击 Create repository
   - 复制 HTTPS URL
3. 设置 remote 并推送：
   ```
   git remote add origin <URL>
   git push -u origin main
   ```

### 第五步：推送后收尾

1. 更新 README 和 pyproject.toml 中的仓库 URL（从占位符改为真实地址）
2. 提交并推送 `docs: 更新仓库URL为真实地址`
3. 为了安全，remote URL 恢复为不含 token 的格式（如果用户用了token方式认证）

## 认证与推送

### 认证方式

GitHub HTTPS 推送需要认证，按以下优先级处理：

1. **Git Credential Manager**（推荐）：Windows/macOS 自带，自动弹出窗口登录
2. **Personal Access Token (PAT)**：嵌入 URL 中，格式 `https://用户名:token@github.com/用户名/仓库.git`
3. **SSH Key**：`git@github.com:用户名/仓库.git`

### 推送失败处理

| 错误 | 原因 | 处理方式 |
|------|------|---------|
| `could not read Username` | 非交互式终端无法弹出认证 | 请用户提供 PAT，或引导在本地终端手动 push |
| `Failed to connect` | 网络问题 | 检查网络/代理，稍后重试 |
| `src refspec main does not match` | 还没有提交 | 先 git add + git commit |
| `remote: Repository not found` | 仓库不存在或权限不足 | 确认仓库URL正确，确认token有repo权限 |
| `error: failed to push some refs` | 远程有本地没有的提交 | 先 git pull --rebase |

## CHANGELOG 规范

使用 **Keep a Changelog** 格式：

```markdown
# Changelog

## [Unreleased]

### Added
- 新功能描述

### Changed
- 变更描述

### Fixed
- 修复描述

## [1.0.0] - 2026-07-02

### Added
- 初始版本发布
```

**版本号规则**：语义化版本 `MAJOR.MINOR.PATCH`

- `MAJOR`：不兼容的 API 改动
- `MINOR`：向下兼容的新功能
- `PATCH`：向下兼容的 bug 修复

**迭代时更新方式**：
- 小改进/fix：增加 PATCH 版本号
- 新功能：增加 MINOR 版本号
- 重大重构：增加 MAJOR 版本号

## 项目结构模板

### Python 项目

```
project-name/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── .env.example
├── skill.md              # （如为Skill项目）
├── package_name/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   └── ...
├── docs/
│   ├── ARCHITECTURE.md
│   ├── USAGE.md
│   └── API.md
└── examples/
    ├── basic_usage.py
    └── advanced_usage.py
```

### 前端/全栈项目

```
project-name/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── package.json
├── .gitignore
├── .env.example
├── src/
│   ├── index.html
│   ├── main.js
│   └── ...
├── docs/
│   ├── ARCHITECTURE.md
│   └── USAGE.md
└── examples/
    └── demo.html
```

## README 模板结构

好的 README 必须包含：

1. **Badge**：语言版本、License、版本号等（shields.io）
2. **项目标题 + 一句话描述**
3. **功能特性**（6-8条，带emoji）
4. **项目结构**（代码块展示目录树）
5. **前置要求**（依赖的工具/环境）
6. **安装步骤**（代码块）
7. **快速开始**（2种以上使用方式：CLI + API）
8. **配置说明**（参数表格）
9. **工作原理**（流程图 + 步骤说明）
10. **注意事项**（常见坑）
11. **文档链接**（docs/ 下的文档）
12. **License**

## 注意事项

### 安全

- **永远不要**在对话中或日志中存储/回显用户的 PAT 或密码
- 推送完成后，将 remote URL 恢复为不含认证信息的格式
- `.env.example` 只放占位符，不放真实值
- `.gitignore` 必须包含 `.env`

### Skill 文件特殊要求

如果项目包含 `.trae/skills/<name>/SKILL.md`：
- **必须以 YAML frontmatter 开头**：文件第一行必须是 `---`，然后是 name/description 等字段，再以 `---` 结束
- **description 字段必须包含触发场景**：说明 "在什么情况下触发这个 skill"
- **Skill 文件必须放在 `.trae/skills/<skill-name>/SKILL.md`** 路径下

**正确示例**：
```markdown
---
name: my-skill
description: "描述功能。Invoke when 用户说XX或做YY。"
metadata:
  requires:
    bins: ["git"]
---

# 标题
...内容...
```

**常见错误**：
- ❌ 文件开头直接写 `# 标题` 而没有 `---`
- ❌ description 没有说明触发场景
- ❌ 路径放错（如根目录下的 `skill.md` 而不是 `.trae/skills/xxx/SKILL.md`）

### 质量

- 代码必须可运行，注释清晰
- 文档必须与代码一致（README 在最后写）
- 示例代码必须能直接运行
- 提交信息必须遵循 Conventional Commits

### 沟通

- 推送前确认仓库 URL 正确
- 大的改动先确认方案再动手
- 推送完成后给出仓库链接
- 每次迭代后说明改了什么、版本号变化

## 给 Vibe Coding 初学者的建议

> 💡 什么是 Vibe Coding？
> 用自然语言描述需求，让 AI 帮你写代码、调试、发布。你负责"想要什么"，AI 负责"怎么做"。

### 1. 描述需求的正确姿势

**坏例子**："帮我做个网站"
→ 太模糊，AI 不知道你要什么类型的网站

**好例子**："帮我做一个个人博客网站，支持Markdown文章、评论功能、暗色模式，用React开发"
→ 明确：类型 + 功能 + 技术栈

**黄金公式**：`什么项目 + 核心功能 + 技术偏好 + 目标用户`

### 2. 迭代思维

不要指望一次就完美。正确的节奏是：
1. 先出一个最小可用版本（MVP）
2. 用起来，发现问题
3. 说"帮我把XX改成YY"、"再加个ZZ功能"
4. 每次迭代一小步，逐步逼近理想状态

### 3. 学会读代码

即使你不写代码，也要能**读懂**AI写的代码。重点看：
- 文件结构（什么代码放哪里）
- 函数/类名（顾名思义）
- 注释（AI写的注释能帮你理解逻辑）

你读得越快，迭代效率越高。

### 4. 善用"为什么"

如果 AI 写的代码你看不懂，直接问：
- "这段代码什么意思？"
- "为什么要这么设计？"
- "有没有更简单的写法？"

理解越深，你提需求的质量就越高。

### 5. 版本管理很重要

Git 不是"高级功能"，是**基础操作**。你需要知道：
- `commit`：保存一个版本快照
- `push`：上传到 GitHub
- `log`：看看历史记录

记住：**每做完一个功能就 commit 一次**，这样改坏了可以回退。

### 6. 文档是给自己写的

README 不是写给别人看的，是写给**三个月后的自己**看的。
如果三个后你忘了怎么用这个项目，README 能帮你快速回忆起来。

### 7. 从小项目开始

不要一上来就做"下一个抖音"。从这些开始：
- 一个待办事项网页
- 一个天气查询工具
- 一个简单的博客

每个小项目都是一次完整的练习：需求 → 编码 → 调试 → 发布。

### 8. 出错是正常的

代码报错、推送失败、功能不工作——这些都是正常的。
关键是：
1. 读错误信息（它已经告诉你哪里错了）
2. 告诉 AI 错误信息
3. 一起修复

每修一个 bug，你就多学一点。

### 9. 发布比完美重要

一个 60 分但已发布的项目，胜过一个 90 分但躺在本地的项目。
- 先上线
- 再迭代
- 持续改进

### 10. 建立你的作品集

每完成一个项目就推到 GitHub：
- 这是你的"作品集"
- 比简历上的"精通XX"有说服力得多
- 半年后回头看，你会惊讶于自己的进步

## 相关链接

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Docs](https://docs.github.com/)
