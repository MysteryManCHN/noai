# 贡献指南

感谢你对 Feishu Meeting Agent 项目的关注！欢迎你参与项目的开发与维护。请在贡献前仔细阅读本指南。

## 目录

- [行为准则](#行为准则)
- [如何提交 Issue](#如何提交-issue)
- [如何提交 Pull Request](#如何提交-pull-request)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [测试说明](#测试说明)
- [文档更新](#文档更新)

## 行为准则

请保持尊重、友善、包容的交流态度。我们希望为每一位贡献者提供一个良好的协作环境。任何形式的人身攻击、骚扰或不当言论都将不被容忍。

## 如何提交 Issue

在提交 Issue 前，请先搜索已有的 Issue，避免重复提交。

### Bug 报告

提交 Bug 时请包含以下信息：

1. **环境信息**：操作系统、Python 版本、lark-cli 版本、使用的 LLM 提供商及模型
2. **复现步骤**：详细描述如何复现该问题
3. **预期行为**：你期望发生什么
4. **实际行为**：实际发生了什么，包含完整的错误日志（注意隐去 API Key 等敏感信息）
5. **最小复现示例**：如有可能，提供最小可复现的代码片段

### 功能建议

提交功能建议时请说明：

1. **使用场景**：你为什么需要这个功能
2. **期望方案**：你希望该功能如何工作
3. **替代方案**：你考虑过的其他实现方式

## 如何提交 Pull Request

1. **Fork 仓库** 并克隆到本地
2. **创建分支**：基于 `main` 分支创建特性分支
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **编写代码**：遵循 [代码规范](#代码规范)
4. **编写测试**：为新功能或修复添加对应的测试用例
5. **运行测试**：确保所有测试通过
   ```bash
   pytest
   ```
6. **提交代码**：遵循 [提交规范](#提交规范)
7. **推送分支** 并在 GitHub 上发起 Pull Request
8. **描述清楚**：在 PR 描述中说明改动内容、动机以及关联的 Issue（如有）

### PR 审查流程

- 至少需要一名维护者审查通过后才能合并
- 请在审查过程中及时响应 Review 意见
- 如有冲突，请在合并前 Rebase 到最新的 `main` 分支

## 开发环境设置

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/feishu-meeting-agent.git
cd feishu-meeting-agent
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. 安装开发依赖

```bash
pip install -e ".[dev]"
```

`dev` 额外依赖包含 `pytest`、`pytest-asyncio`、`ruff`、`mypy` 等开发工具。

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入测试用的 API Key
```

### 5. 安装 pre-commit 钩子（可选）

```bash
pre-commit install
```

## 代码规范

### Python 风格

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 编码风格
- 使用 4 个空格缩进，禁止使用 Tab
- 单行最大长度 100 字符
- 使用 `ruff` 进行格式化和静态检查
  ```bash
  ruff check .
  ruff format .
  ```

### 类型注解

- 所有公共函数和方法必须添加类型注解
- 使用 `mypy` 进行类型检查
  ```bash
  mypy meeting_agent
  ```

### 命名约定

- 模块、包名：`snake_case`
- 类名：`PascalCase`
- 函数、变量：`snake_case`
- 常量：`UPPER_SNAKE_CASE`
- 私有成员：以单下划线开头 `_private`

### 异步编程

- 涉及 I/O 的操作使用 `async/await`
- 禁止在异步上下文中使用阻塞调用
- 使用 `asyncio` 提供的并发原语，避免裸 `threading`

### 日志

- 使用标准库 `logging`，不要直接 `print`
- 日志内容不应包含 API Key、用户隐私等敏感信息
- 关键操作（入会、离会、调用 LLM）应记录 INFO 级别日志

## 提交规范

我们遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/v1.0.0/) 规范。

### 提交格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构（既不是新增功能也不是修复 Bug） |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建、依赖、工具链等杂项 |
| `ci` | CI 配置变更 |

### 示例

```
feat(summary): 支持流式输出增量总结
fix(meeting): 修复离会时未清理监听任务的问题
docs(readme): 补充 DeepSeek 配置示例
```

## 测试说明

### 运行测试

```bash
# 运行全部测试
pytest

# 运行指定模块测试
pytest tests/summary/

# 显示详细输出
pytest -v

# 生成覆盖率报告
pytest --cov=meeting_agent --cov-report=html
```

### 测试要求

- 新增功能必须附带单元测试
- Bug 修复需提供回归测试
- 测试覆盖率不应低于现有水平
- 使用 `pytest.mark.asyncio` 标记异步测试
- 对外部依赖（lark-cli、LLM API）使用 Mock，不要在 CI 中调用真实接口

### 测试组织

```
tests/
├── meeting/            # 会议模块测试
├── summary/            # 总结模块测试
├── conftest.py         # 公共 fixtures
└── test_main.py        # 入口测试
```

## 文档更新

如你的 PR 涉及以下变更，请同步更新相关文档：

- 新增/修改公共 API → 更新 `docs/API.md`
- 修改使用方式 → 更新 `docs/USAGE.md`
- 修改架构 → 更新 `docs/ARCHITECTURE.md`
- 新增功能 → 更新 `README.md` 和 `CHANGELOG.md`

### CHANGELOG 更新

在 `CHANGELOG.md` 的 `[Unreleased]` 段落下按以下分类记录变更：

- `Added` - 新增功能
- `Changed` - 对现有功能的变更
- `Deprecated` - 即将移除的功能
- `Removed` - 已移除的功能
- `Fixed` - Bug 修复
- `Security` - 安全相关修复

## 联系方式

- 提交 Issue：[GitHub Issues](https://github.com/your-username/feishu-meeting-agent/issues)
- 加入早鸟群：遇 VC Agent 权限相关问题（error code 20017）可联系维护者加入

再次感谢你的贡献！
