# Profile README 设计与维护

仓库为公开的 [helloe365/helloe365](https://github.com/helloe365/helloe365)，默认分支为 main。根目录 README.md 是个人主页唯一入口；本文件记录设计、数据口径和维护方式。

## 1. 设计决策

1. **桌面阅读优先**：按本次确认保留项目 2×2、统计 1×2。49% 在 GitHub 手机页面不会自动变成 100%；正文摘要负责窄屏阅读，不宣称自动单列。
2. **首屏直接到作品**：保留 hello2world、湖南大学本科在读和长沙，把 CrackPDFPassword、全部项目、联系我放在首屏；移除延迟显字、粒子、光晕和索要 star 的页脚文案。
3. **保留终端记忆点**：正文在加载时全部可见，仅光标闪动三次。About 讲方向、动机和项目；技术栈单独列能力清单。
4. **一套 Tokyo Night**：青用于导航与标题、紫用于技能、绿用于正向计数。亮色强调色进一步加深，自绘 SVG 正文对两种表面的最低对比度为 4.93:1。
5. **减少重复与噪声**：5 个二级区块，20 个徽章；加上 8 个技能图标也只有 28 项。六行技能表居中，贡献细节折叠，取消不透明的奖杯等级和未证实的性能指标。
6. **数字保留证据**：star/fork、语言字节与贡献来自 GitHub API；stats/data.json 保存渲染输入。请求失败即退出，不用零值替代缺失数据，也不把失败运行标记成刷新成功。
7. **解决规格内的排版冲突**：自绘卡片使用 44/16、28/16 或 20/16px，每张图最多两档字号且都是 4 的倍数。徽章全站统一 flat，包括 Contact；徽章保留固有尺寸，避免百分比放大导致的布局失真。
8. **保留真实的托管边界**：自绘资产全部使用仓库相对路径。Shields 与 Skill Icons 使用官方双主题 URL；Snake 使用 output 分支的绝对 URL。这些是“所有图片相对路径”的明确例外。

## 2. README 与嵌入规则

- README.md 必须位于公开同名仓库 helloe365/helloe365 的默认分支根目录。
- 所有图片都由 picture 包裹，light source 指向亮色资源，img 默认使用暗色资源。
- 本仓库自绘 SVG 的暗色文件沿用原名，亮色增加 -light 后缀；3D 图保留已有的两个历史文件名。
- 首屏、终端、分隔线、页脚和纵向图表宽度为 100%；四张项目卡、统计卡对和图标行为 49%；不指定 img height。
- Shields 徽章是固有尺寸的例外：其高度由服务固定为 20px，避免把小徽章拉伸成大卡片。不同主题的 labelColor、logoColor 一并指定。
- 3D 与 Snake 不依赖第三方在线出图服务，均由本仓库 Actions 运行开源生成程序。
- fork 后相对资产仍可读取；若改成自己的 Profile，需使用自己的公开同名仓库，并修改项目清单、身份、邮箱及 Snake 的账号 URL。

## 3. SVG 文件与规格

成对资源只改变语义颜色，布局、文本与数据完全相同。自绘卡片均为 12px 圆角、1px 描边、系统字体栈 -apple-system, "Segoe UI", Roboto, sans-serif。

| 文件（暗 / 亮） | viewBox | 字号 | 改造内容 |
|---|---|---|---|
| assets/hero.svg / hero-light.svg | 0 0 720 216 | 44 / 16 | 姓名、短定位与真实身份即刻出现；来源—检索—回答示意 |
| assets/terminal.svg / terminal-light.svg | 0 0 720 252 | 16 | 保留终端形式，输出始终可见，光标 4.5 秒后停止 |
| assets/divider.svg / divider-light.svg | 0 0 720 24 | 无 | 统一 1px 分隔线，移除发光动画 |
| assets/footer.svg / footer-light.svg | 0 0 720 96 | 28 / 16 | 简短收尾，移除求 star 文案 |
| stats/stats.svg / stats-light.svg | 0 0 400 165 | 20 / 16 | 六项可核查指标，时间范围写进标签与正文 |
| stats/top-langs.svg / top-langs-light.svg | 0 0 400 165 | 20 / 16 | 同色系横条，前三种语言与 Other |
| stats/activity.svg / activity-light.svg | 0 0 720 240 | 20 / 16 | 周汇总折线，零值和单周输入可渲染 |
| stats/trophies.svg / trophies-light.svg | 0 0 720 172 | 28 / 16 | 实际计数与明确阈值，不做能力评级 |
| stats/pin-CrackPDFPassword.svg / pin-CrackPDFPassword-light.svg | 0 0 400 228 | 20 / 16 | 授权 PDF 恢复、检查点续跑、两项技术、实时 star/fork |
| stats/pin-CupLens.svg / pin-CupLens-light.svg | 0 0 400 228 | 20 / 16 | 赛事预测、模型与来源快照、三项技术、实时计数 |
| stats/pin-RagAgent.svg / pin-RagAgent-light.svg | 0 0 400 228 | 20 / 16 | 检索问答、幂等入库、三项技术、实时计数 |
| stats/pin-AdaptiveFinancialFraudDetectionSystem.svg / pin-AdaptiveFinancialFraudDetectionSystem-light.svg | 0 0 400 228 | 20 / 16 | 长仓库名分两行，VAE 与 DevNet 结果说明 |
| profile-3d-contrib/profile-night-rainbow.svg / profile-season-animate.svg | 0 0 1280 850 | 13 / 16 / 20.8 / 21.67 / 24 / 32（上游） | 保留上游真实几何、数据与字号，统一背景、系统字体和紫色语言图例，展开 CSS 属性；贡献格保留绿色强度编码 |
| output 分支 github-contribution-grid-snake-dark.svg / github-contribution-grid-snake.svg | 当前为 -16 -32 880 192 | 无 | 青色蛇身与同色系绿色贡献格；宽度随贡献日历变化 |

主色：暗色背景 #0b0d17、卡片 #1a1b27、描边 #2a2e45；亮色背景 #f7f9fc、卡片 #ffffff、描边 #e3e8f0。亮色青 #217594、紫 #7256a8、绿 #48752c；#2f9bc4 本身不足以保证白底小字 4.5:1，因此未直接采用。

## 4. 生成脚本与数据口径

| 文件 / 函数 | 职责 |
|---|---|
| scripts/generate_assets.py：THEMES、text、svg | 共用颜色、字体、圆角与安全 SVG 文本转义 |
| hero_svg、terminal_svg、divider_svg、footer_svg | 生成 8 张离线、确定性的插图 |
| contribution_settings | 同一套颜色生成 .github/profile-3d-settings.json |
| style_contribution_svg | 给现有 3D 产物统一字体与图例颜色；不改变数据或贡献格几何 |
| scripts/generate_stats.py：collect_snapshot | 分页抓取自有公开非 fork 仓库、语言字节和 GitHub 贡献日历 |
| validate_snapshot | 拒绝缺失项目、负数、空日历与不一致的贡献合计 |
| stats_svg、langs_svg、pin_svg、activity_svg、trophies_svg | 从同一份输入绘制 16 张亮暗统计图 |
| render | 先校验和渲染所有图，再写文件；同一输入字节一致 |
| scripts/check_links.py | 验证图片、本地路径、锚点、普通外链、邮箱格式；使用实际 timeout |

~~~powershell
# 离线重放：无需登录、无网络、无额外 Python 依赖
python scripts/generate_assets.py
python scripts/generate_stats.py --snapshot stats/data.json

# 实时刷新：环境中已有有效 GITHUB_TOKEN 时
python scripts/generate_stats.py

# 完整链接检查；邮箱只验格式，不代表投递测试
python scripts/check_links.py --timeout 20

# 本地离线检查会明确报告跳过了哪些远程 URL
python scripts/check_links.py --offline
~~~

统计范围：

- Stars / forks / repos：所有自有公开、非 fork 仓库；包含归档仓库，不隐藏低计数。
- Commits / PRs / issues：GitHub contributionsCollection 最近一年的可见贡献，不宣称全历史总量。
- 语言：GitHub Languages API 的仓库代码字节；前三种语言加 Other，Notebook 表示 Jupyter Notebook，不等同技能熟练度。
- 活跃度：contributionCalendar 逐日计数按周求和，首尾周可能不完整。仅保留 GitHub 可见的汇总数据。
- 里程碑：实际 stars、项目数、PR 数与活跃天数，显示达到的 1/10/100/1000/10000 阈值。不是 GitHub 官方成就。
- 功能亮点来自四个项目的公开 README。没有把项目文档中的宣传语或未复测的性能数字写进个人主页。

## 5. Workflows

| Workflow | 北京时间计划 | 产物与验证 |
|---|---|---|
| generate-stats.yml | 每日 10:00 | assets/*.svg、stats/*.svg、stats/data.json、3D 配色 JSON；离线重放 SHA-256、链接检查通过后才提交 |
| profile-3d-contrib.yml | 每日 08:30 | 两张兼容旧文件名的 3D 图；统一字体/颜色、解析 SVG，并将同次生成的基础插图与配色一并提交 |
| snake.yml | 每日 08:00 | 亮暗 SVG 写入 output 分支；显式 contents: write，并保留分支历史 |

以上时间是 cron 计划，GitHub 可能延迟调度。三个 workflow 都支持 workflow_dispatch；相关源码变更还会在 main/master 推送时触发。使用 Actions 自动注入的 GITHUB_TOKEN，无需额外配置个人访问令牌。

两个写默认分支的 workflow 共享 concurrency group，防止同时提交互相覆盖。无变更时退出；生成、校验或提交失败不会被 “No changes” 吞掉。

generate-stats.yml 的 profile-evidence artifact 保存本次输入与 SHA-256。要比较本地与 Actions：

1. 在自己的公开同名仓库默认分支保存这些文件。
2. 在 Actions 页面手动运行三个 workflow。
3. 下载 profile-evidence，用其中的 data.json 本地重放。
4. 对照 artifact 中的校验和；应逐字节一致。

仅完成本地编辑不会更新线上 Profile 或 output 分支。

## 6. 三断点验收

本次使用 GitHub Markdown API 清洗后的内容，以及当前 GitHub 个人页 DOM/CSS 做浏览器预览；远程图片已实际请求校验，并在预览中使用同一内容的本地副本。Snake 预览使用本次实际运行上游程序生成的新配色文件。该预览不是已经发布的 GitHub 页面。

| 视口 | 当前个人页内容宽度 | 双栏卡片正文约值 | 本次检查 / 预期 |
|---|---:|---:|---|
| 1280px | 831px | 16.3px | 亮暗图均加载；项目 2×2、统计并排等高；无横向溢出，图内文字无裁切 |
| 768px | 383px | 7.5px | GitHub 侧栏压缩 README，保持双栏；正文摘要按 GitHub 的 14px 阅读；无横向溢出 |
| 375px | 278px | 5.5px | 卡片仍是双栏小图；项目说明、身份和联系方式靠正文阅读；徽章自然换行、表格不溢出 |

768px 与 375px 的图内文字不满足原始“至少 14px / 自动单列”条件。这里按用户确认的“电脑可读优先”接受此限制，没有用未经支持的 CSS 或虚假的断点声明掩盖它。

逐项检查：

- [x] 亮 / 暗两套 × 1280 / 768 / 375，共 6 张截图。
- [x] 各档没有横向溢出，项目顺序保持一致，图片全部加载。
- [x] 5 个二级区块；20 个 Shields 徽章；8 个 Skill Icons 图标。
- [x] 全部图片有明确 alt；身份、项目和联系方式均有独立正文，技术徽章有语义化 alt。
- [x] 24 张自绘 SVG 的文字无出界或相互覆盖，字号为 4 的倍数。
- [x] API 实时抓取、离线重放和异常输入检查已执行。
- [x] 上游 3D 与 Snake 程序已在本地运行；3D 配色处理幂等。
- [ ] 发布后的 GitHub 网页版：再检查主题切换、Camo 图片加载、导航与 output 分支图片。
- [ ] GitHub App：用实际设备检查 1280/768/375 对应布局、亮暗切换及链接跳转。
- [ ] 新版 GitHub Actions：发布后手动运行，核对本地与 artifact 的相同输入哈希。

生成程序本地运行通过，不等于验证过 GitHub runner 的实际令牌权限、远程提交或 GitHub App。

## 7. 上游与维护

- [GitHub Profile README 文档](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-github-profile/customizing-your-profile/managing-your-profile-readme)
- [GitHub Profile 3D Contributions](https://github.com/yoshi389111/github-profile-3d-contrib)：复用 v0.9.3 的数据与绘图。
- [Platane/snk](https://github.com/Platane/snk)：复用 v3 的贡献路径与 SVG 动画。
- [Shields](https://shields.io)、[Skill Icons](https://skillicons.dev)：非核心装饰内容有第三方可用性边界。

本人身份、联系方式或代表项目变化时更新 README 和脚本中的静态文案；数字由 Actions 更新，不另写每周维护的计数。
