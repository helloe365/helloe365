# 🚀 GitHub Profile 主页部署指南

本目录是你的 GitHub 个人主页仓库（`helloe365/helloe365`）的完整内容，风格参考 [BEPb/BEPb](https://github.com/BEPb/BEPb)，并针对你的技术栈（Python / AI / LLM / 安全）做了个性化定制。

## 文件说明

| 文件 | 作用 |
|---|---|
| `README.md` | 主页内容本体（徽章、技能表、统计卡片、精选项目、动画等） |
| `.github/workflows/snake.yml` | 每天自动生成"贪吃蛇吃贡献格"动画（存放到 `output` 分支） |
| `.github/workflows/profile-3d-contrib.yml` | 每天自动生成 3D 贡献图（存放到 `profile-3d-contrib/` 目录） |

## 部署步骤

### 1. 创建同名仓库

打开 <https://github.com/new> 新建仓库：

- **Repository name 必须填 `helloe365`**（与你的 GitHub 用户名完全一致，GitHub 才会把它识别为个人主页）
- 可见性选择 **Public**
- **不要**勾选 "Add a README file" 等任何初始化选项

### 2. 推送本目录

在本目录打开终端（PowerShell），依次执行：

```bash
git init
git add .
git commit -m "feat: beautify github profile"
git branch -M main
git remote add origin https://github.com/helloe365/helloe365.git
git push -u origin main
```

### 3. 启用并触发 GitHub Actions

1. 推送后打开仓库的 **Actions** 标签页
2. 若出现黄色提示条，点击 **"I understand my workflows, go ahead and enable them"**
3. 左侧分别选择 `Generate Contribution Snake` 和 `GitHub Profile 3D Contributions`，点击 **Run workflow** 手动触发一次
4. 等待约 1~2 分钟运行完成后，刷新 <https://github.com/helloe365> 即可看到完整效果

> ⚠️ 首次运行 Action 之前，README 中的贪吃蛇和 3D 贡献图会显示为裂图，这是正常现象——这两个文件由 Action 生成，需要先跑一次 workflow。

## 个性化修改

- **打字机文案**：修改 README 顶部 `readme-typing-svg.demolab.com` 链接中的 `lines=` 参数，多行用 `;` 分隔，中文需 URL 编码
- **配色主题**：所有统计卡片统一使用 `tokyonight` 主题，可全局替换为 `radical`、`dracula`、`synthwave` 等（见 [github-readme-stats 主题列表](https://github.com/anuraghazra/github-readme-stats#themes)）
- **头部波浪**：修改 `capsule-render.vercel.app` 链接中的 `color=0:xxx,50:xxx,100:xxx` 渐变色（十六进制）
- **技能徽章**：直接增删技术栈表格中的 shields.io 徽章，或修改 `skillicons.dev` 链接的 `i=` 参数
- **精选项目**：替换 pin 卡片的 `repo=` 参数为你想展示的项目

## 致谢

- [BEPb/BEPb](https://github.com/BEPb/BEPb) — 设计灵感来源
- [anuraghazra/github-readme-stats](https://github.com/anuraghazra/github-readme-stats) — 统计卡片与项目卡片
- [DenverCoder1/readme-typing-svg](https://github.com/DenverCoder1/readme-typing-svg) — 打字机动画
- [Platane/snk](https://github.com/Platane/snk) — 贪吃蛇贡献动画
- [yoshi389111/github-profile-3d-contrib](https://github.com/yoshi389111/github-profile-3d-contrib) — 3D 贡献图
- [ryo-ma/github-profile-trophy](https://github.com/ryo-ma/github-profile-trophy) — 个人奖杯
- [Ashutosh00710/github-readme-activity-graph](https://github.com/Ashutosh00710/github-readme-activity-graph) — 活跃度折线图
