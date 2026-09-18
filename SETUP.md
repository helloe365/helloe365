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
- **统计卡片**：所有统计/语言/项目卡片均为本地 SVG（`stats/` 目录），由 `scripts/generate_stats.py` 生成 dark（tokyonight）+ light 双主题，配色修改脚本中的 `THEMES` 字典即可
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
- [Ashutosh00710/github-readme-activity-graph](https://github.com/Ashutosh00710/github-readme-activity-graph) — 活跃度折线图（公共实例已停摆，可自部署后恢复）

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
