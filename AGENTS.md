# Repository Guidelines

## 项目结构与模块组织
- `src/ui/`: React 19 + Tailwind 的渲染层（组件、hooks、store、render）。
- `src/electron/`: Electron 主进程与 IPC（`main.ts`、`ipc-handlers.ts`、`preload.cts`）。
- `assets/` 与 `src/ui/assets/`: 静态资源与宣传素材。
- `dist-electron/`: Electron 构建产物。
- `test/`: 预留测试目录（当前为空）。

## 构建、测试与开发命令
- `bun install`: 安装依赖。
- `bun run dev`: 启动 Vite + Electron（本地开发）。
- `bun run dev:react`: 仅启动前端 UI。
- `bun run dev:electron`: 仅启动 Electron 主进程。
- `bun run build`: 类型检查 + 前端构建。
- `bun run lint`: ESLint 检查。
- `bun run dist:mac` / `bun run dist:win` / `bun run dist:linux`: 平台打包发布。

## 编码风格与命名约定
- 语言：TypeScript + React，ESM 模块。
- 缩进与引号保持与同文件一致；以 ESLint 结果为准（见 `eslint.config.js`）。
- 组件使用 PascalCase（如 `StartSessionModal`），hooks 用 `useX`（如 `useIPC`）。
- 状态管理集中在 `src/ui/store/`，共享类型放在 `src/ui/types.ts` 或 `src/electron/types.ts`。

## 测试指南
- 目前无统一测试框架与脚本；新增测试需同时补充 `package.json` scripts。
- 建议放在 `test/`，并在 PR 中写明运行方式与覆盖范围。

## 提交与 PR 规范
- 提交信息以简短动作为主，常见格式：`fix(scope): desc`、`Update README.md`；保持一致即可。
- PR 需包含：改动说明、关联 issue（若有）、UI 变更截图/录屏、验证结果（如 `bun run lint`）。

## 配置与安全
- 本地密钥/模型配置使用个人环境（如 `~/.claude/settings.json` 或 `.env`），不要提交到仓库。
- 新增环境变量请在 README 中说明用途与示例。
