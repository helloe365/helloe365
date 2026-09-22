# 🚀 GitHub Profile 主页部署指南

本目录是你的 GitHub 个人主页仓库（`helloe365/helloe365`）的完整内容，风格参考 [BEPb/BEPb](https://github.com/BEPb/BEPb)，并针对你的技术栈（Python / AI / LLM / 安全）做了个性化定制。

## 文件说明

| 文件 | 作用 |
|---|---|
| `README.md` | 主页内容本体（徽章、技能表、统计卡片、精选项目、动画等） |
| `scripts/generate_assets.py` | 生成 `assets/` 下手写的动画 SVG（头图、终端卡、分割线、页脚），离线、确定性输出 |
| `scripts/generate_stats.py` | 生成 `stats/` 下的统计/语言/项目/活跃度/奖杯卡片（需 GITHUB_TOKEN） |
| `scripts/check_links.py` | 一键检查 README 里每张图是否能正常渲染 |
| `.github/workflows/generate-stats.yml` | 每天重新生成 `stats/` 卡片 |
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

顶部头图、终端卡片、分割线、页脚都是**手写的动画 SVG**，由 `scripts/generate_assets.py` 生成，不依赖任何外部服务（capsule-render / readme-typing-svg 这类 Vercel 实例已全部移除，不会再裂图）。改完跑一次即可：

```bash
python scripts/generate_assets.py   # 无需网络，无需 token
python scripts/check_links.py       # 确认 README 里每张图都能渲染
```

- **头图文案**：改脚本里的 `HERO_CMD` / `HERO_TITLE` / `HERO_TAG`
- **终端卡内容**：改脚本里的 `SESSION` 列表，`True` 为逐字打出的命令行，`False` 为整行弹出的输出
- **轮换座右铭**：改脚本里的 `MOTTOS` 列表（终端卡 `echo $MOTTO` 的输出）。每轮 20 秒循环展示一条，逐字打出后保持到本轮结束，下一轮自动换下一条；条数不限，中英文均可
- **配色**：改脚本顶部的 `THEMES` 字典（`""` 为暗色 tokyonight，`"-light"` 为亮色），两套主题同源生成，不会跑偏
- **统计卡片**：均为本地 SVG（`stats/` 目录），由 `scripts/generate_stats.py` 生成 dark + light 双主题
- **技能徽章**：直接增删技术栈表格中的 shields.io 徽章，或修改 `skillicons.dev` 链接的 `i=` 参数
- **精选项目**：改 `generate_stats.py` 里的 `FEATURED_REPOS`（仓库名 + 一句话简介）

> 动画用的是 SMIL（`<animate>` / `<animateTransform>`）。GitHub 通过 `<img>` 加载 SVG，会执行 SVG 内部的 SMIL 和 CSS 动画，但会屏蔽脚本和外部资源——所以脚本里只用系统等宽字体，不引 Web Font。

## 致谢

- [BEPb/BEPb](https://github.com/BEPb/BEPb) — 设计灵感来源
- [anuraghazra/github-readme-stats](https://github.com/anuraghazra/github-readme-stats) — 统计卡片与项目卡片
- [Platane/snk](https://github.com/Platane/snk) — 贪吃蛇贡献动画
- [yoshi389111/github-profile-3d-contrib](https://github.com/yoshi389111/github-profile-3d-contrib) — 3D 贡献图
- [ryo-ma/github-profile-trophy](https://github.com/ryo-ma/github-profile-trophy) — 个人奖杯
- [Ashutosh00710/github-readme-activity-graph](https://github.com/Ashutosh00710/github-readme-activity-graph) — 活跃度折线图（公共实例已停摆，现为本地生成）

---

## 🛠 统计卡片裂图问题（已解决 ✅）

> 统计/语言/项目卡片、**贡献活跃度折线图**、**奖杯墙**已全部改为**本地 SVG**（`stats/` 目录，GitHub Actions 每日更新；活跃度图与奖杯通过 GraphQL 生成），不再依赖任何公共实例，裂图问题已根除。

### 一键部署 github-readme-stats（恢复 Stats / Top Langs / 项目卡片）

1. 打开 <https://vercel.com>，用 GitHub 账号登录（免费）
2. 打开 <https://vercel.com/new/clone?repository-url=https://github.com/anuraghazra/github-readme-stats>
3. 直接点 **Deploy**（无需任何环境变量）
4. 部署完成后拿到形如 `github-readme-stats-xxxx.vercel.app` 的域名
5. 将本仓库 `README.md` 中的 `github-readme-stats.vercel.app` 全局替换为你的域名，push 即可

### 奖杯墙说明（已本地化）

`stats/trophies.svg` 由 `scripts/generate_stats.py` 生成，等级阈值完整复刻自 [ryo-ma/github-profile-trophy](https://github.com/ryo-ma/github-profile-trophy) 的开源源码（`src/trophy.ts`），含 7 个基础奖杯 + 达成才显示的隐藏奖杯（如 Rainbow Lang User、Village Elder）。无需自部署任何服务。
