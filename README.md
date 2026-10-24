# gzh-daily-push

GitHub Actions 每天北京时间 08:00 左右抓取 GitHub Trending 前 8 个仓库，通过 Server酱 推送到微信。

- 脚本只用 Python 标准库，无需安装依赖
- SendKey 存在仓库 Secret `SCT_SENDKEY` 里，不进代码
- 手动触发：Actions 页面 → GitHub Trending Daily Push → Run workflow
- cron 为 UTC 00:00，实际触发可能有 0-30 分钟延迟

结构：

- `push.py` 抓取 + 推送主脚本
- `.github/workflows/daily-push.yml` 定时工作流
