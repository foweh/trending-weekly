# GitHub Trending Weekly

> 每周自动生成一份 GitHub Trending 热门仓库简报，涵盖多种编程语言。

[![GitHub Stars](https://img.shields.io/github/stars/foweh/trending-weekly?style=social)]()
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/foweh/trending-weekly/weekly.yml)]()
[![License MIT](https://img.shields.io/badge/license-MIT-blue)]()

---

## 它能做什么

每周一自动运行 GitHub Actions，抓取 GitHub Trending 上 15 种主流语言的热门仓库，生成三种格式的报告：

| 格式 | 说明 |
|------|------|
| Markdown | 可直接用于 Issue / Wiki |
| HTML | 美观的网页，可部署到 GitHub Pages |
| JSON | 结构化数据，供二次开发 |

---

## 在线浏览

部署到 GitHub Pages 后，访问：

```
https://foweh.github.io/trending-weekly/latest.html
```

---

## 本地运行

```bash
git clone https://github.com/foweh/trending-weekly.git
cd trending-weekly

pip install -r requirements.txt

# 获取所有语言的 trending
python trending.py --all-langs

# 或只获取特定语言
python trending.py --lang python

# 指定输出目录
python trending.py --all-langs --output-dir ./my-output
```

---

## 支持的语言

Python / JavaScript / TypeScript / Go / Rust / Java / C++ / Ruby / Swift / Kotlin / Vue / React / Dockerfile / Shell / C

## 输出目录结构

```
output/
├── latest.md          # 最新一期 Markdown
├── latest.html        # 最新一期 HTML
├── latest.json        # 最新一期 JSON
├── weekly-12.md       # 第 12 周
├── weekly-12.html
└── weekly-12.json
```

## 技术栈

- Python + requests (HTML 解析)
- Jinja2 (模板引擎)
- GitHub Actions (定时触发 + 自动部署 Pages)

## License

MIT
