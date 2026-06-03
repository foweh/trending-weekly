"""
GitHub Trending Weekly - 获取过去一周按语言分类的热门仓库

使用方法:
    python trending.py                   # 获取所有语言的 trending
    python trending.py --lang python     # 只获取 Python
    python trending.py --all-langs       # 获取多种语言的 trending
    python trending.py --output-dir ./output
"""

import argparse
import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader


class TrendingFetcher:
    """从 GitHub Trending 页面抓取热门仓库"""

    TRENDING_URL = "https://github.com/trending/{lang}?since=weekly"

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; TrendingWeekly/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        })

    def fetch_trending(self, language: str = "") -> list[dict]:
        """抓取指定语言的 Trending 仓库列表"""
        url = self.TRENDING_URL.format(lang=language)
        print(f"[fetch] {url}")

        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()

        repos = []
        # 解析 HTML 提取仓库信息
        html = resp.text

        # 每个仓库在 <article class="Box-row"> 中
        articles = re.findall(
            r'<article class="Box-row[^"]*"[^>]*>(.*?)</article>',
            html, re.DOTALL
        )

        for article in articles:
            repo = self._parse_article(article, language)
            if repo:
                repos.append(repo)

        return repos

    def _parse_article(self, article: str, language: str) -> dict | None:
        """解析单个仓库的 HTML"""

        # 仓库名: <h2><a href="/owner/repo">
        name_match = re.search(
            r'<h2[^>]*>.*?<a[^>]*href="/([^"]+)"[^>]*>',
            article, re.DOTALL
        )
        if not name_match:
            return None

        full_name = name_match.group(1).strip()

        # 描述: <p class="col-9 ...">text</p>
        desc_match = re.search(
            r'<p[^>]*class="col-9[^"]*"[^>]*>(.*?)</p>',
            article, re.DOTALL
        )
        description = ""
        if desc_match:
            description = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()

        # Star 数
        stars_match = re.search(
            r'<a[^>]*href="/[^"]*/stargazers"[^>]*>.*?(\d[\d,.]*[kKmMbB]?)</a>',
            article, re.DOTALL
        )
        stars = 0
        if stars_match:
            stars = self._parse_num(stars_match.group(1))

        # Fork 数
        forks_match = re.search(
            r'<a[^>]*href="/[^"]*/forks"[^>]*>.*?(\d[\d,.]*[kKmMbB]?)</a>',
            article, re.DOTALL
        )
        forks = 0
        if forks_match:
            forks = self._parse_num(forks_match.group(1))

        # 今日新增 Star
        today_stars_match = re.search(
            r'<span[^>]*class="d-inline-block float-sm-right"[^>]*>\s*([\d,.]+\s*stars\s*today)\s*</span>',
            article, re.DOTALL
        )
        today_stars = 0
        if today_stars_match:
            num_match = re.search(r'([\d,.]+)', today_stars_match.group(1))
            if num_match:
                today_stars = self._parse_num(num_match.group(1))

        # 语言
        lang_match = re.search(
            r'<span[^>]*itemprop="programmingLanguage"[^>]*>([^<]+)</span>',
            article
        )
        repo_lang = ""
        if lang_match:
            repo_lang = lang_match.group(1).strip()
        if not repo_lang:
            repo_lang = language if language else "Unknown"

        return {
            "name": full_name,
            "url": f"https://github.com/{full_name}",
            "description": description,
            "language": repo_lang,
            "stars": stars,
            "forks": forks,
            "today_stars": today_stars,
            "owner": full_name.split("/")[0],
            "repo": full_name.split("/")[1] if "/" in full_name else full_name,
        }

    def _parse_num(self, text: str) -> int:
        """解析带 k/m/b 后缀的数字"""
        text = text.strip().replace(",", "")
        if text.lower().endswith("k"):
            return int(float(text[:-1]) * 1000)
        if text.lower().endswith("m"):
            return int(float(text[:-1]) * 1000000)
        if text.lower().endswith("b"):
            return int(float(text[:-1]) * 1000000000)
        try:
            return int(float(text))
        except ValueError:
            return 0

    def fetch_all_languages(self, languages: list[str]) -> dict[str, list[dict]]:
        """获取多种语言的 Trending"""
        result = {}
        for lang in languages:
            try:
                repos = self.fetch_trending(lang)
                result[lang] = repos
                print(f"  -> found {len(repos)} repos for '{lang}'")
            except Exception as e:
                print(f"  -> error fetching '{lang}': {e}")
                result[lang] = []
            time.sleep(1)  # 防止被限流
        return result

    def generate_report(self, data: dict[str, list[dict]], output_format: str = "all"):
        """生成报告"""
        env = Environment(loader=FileSystemLoader("templates"))
        week_number = datetime.now().isocalendar()[1]
        date_range = self._get_date_range()
        total_repos = sum(len(v) for v in data.values())

        context = {
            "week_number": week_number,
            "date_range": date_range,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
            "total_repos": total_repos,
            "languages": data,
            "lang_count": len(data),
        }

        if output_format in ("md", "all"):
            md = env.get_template("weekly.md.j2").render(**context)
            md_path = self.output_dir / f"weekly-{week_number}.md"
            md_path.write_text(md, encoding="utf-8")
            # 也写一份 latest
            (self.output_dir / "latest.md").write_text(md, encoding="utf-8")
            print(f"[write] {md_path}")

        if output_format in ("html", "all"):
            html = env.get_template("weekly.html.j2").render(**context)
            html_path = self.output_dir / f"weekly-{week_number}.html"
            html_path.write_text(html, encoding="utf-8")
            (self.output_dir / "latest.html").write_text(html, encoding="utf-8")
            print(f"[write] {html_path}")

        # JSON 数据（供二次消费）
        json_path = self.output_dir / f"weekly-{week_number}.json"
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        (self.output_dir / "latest.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[write] {json_path}")

    def _get_date_range(self) -> str:
        """获取最近一周的日期范围字符串"""
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        return f"{week_ago.strftime('%b %d')} - {today.strftime('%b %d, %Y')}"


def main():
    parser = argparse.ArgumentParser(description="GitHub Trending Weekly Reporter")
    parser.add_argument("--lang", default="", help="特定语言")
    parser.add_argument("--all-langs", action="store_true", help="获取多种语言")
    parser.add_argument("--output-dir", default="output", help="输出目录")
    parser.add_argument("--format", default="all", choices=["md", "html", "all"])
    args = parser.parse_args()

    fetcher = TrendingFetcher(output_dir=args.output_dir)

    # 要抓取的语言列表
    ALL_LANGS = [
        "python", "javascript", "typescript", "go", "rust",
        "java", "c++", "ruby", "swift", "kotlin",
        "vue", "react", "dockerfile", "shell", "c",
    ]

    if args.all_langs:
        data = fetcher.fetch_all_languages(ALL_LANGS)
    elif args.lang:
        data = {args.lang: fetcher.fetch_trending(args.lang)}
    else:
        # 默认只获取 trending overall（无语言过滤）
        data = {"all": fetcher.fetch_trending("")}

    fetcher.generate_report(data, output_format=args.format)
    print("[done] 报告生成完成！")


if __name__ == "__main__":
    main()
