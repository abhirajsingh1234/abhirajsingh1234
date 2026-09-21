#!/usr/bin/env python3
"""
GitHub Stats README Auto-Updater
Fetches live stats via GitHub API and rewrites the stats table in README.md
between <!-- START_STATS --> and <!-- END_STATS --> markers.
"""

import os
import re
import requests
from datetime import datetime, timezone


def get_github_stats(username: str, token: str) -> dict | None:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    try:
        user_resp = requests.get(
            f"https://api.github.com/users/{username}",
            headers=headers,
            timeout=10,
        )
        user_resp.raise_for_status()
        user_data = user_resp.json()

        repos = []
        page = 1
        while True:
            r = requests.get(
                f"https://api.github.com/users/{username}/repos",
                headers=headers,
                params={"per_page": 100, "page": page},
                timeout=10,
            )
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            repos.extend(batch)
            page += 1

        public_repos = len([r for r in repos if not r.get("private")])
        total_stars = sum(r.get("stargazers_count", 0) for r in repos)
        total_forks = sum(r.get("forks_count", 0) for r in repos)

        return {
            "repos": public_repos,
            "stars": total_stars,
            "forks": total_forks,
            "followers": user_data.get("followers", 0),
            "following": user_data.get("following", 0),
        }

    except Exception as e:
        print(f"❌ Error fetching stats: {e}")
        return None


def update_readme(username: str, token: str) -> bool:
    stats = get_github_stats(username, token)
    if not stats:
        return False

    now_utc = datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p UTC")

    new_block = f"""<!-- START_STATS -->
## 📊 GitHub Statistics

<div align="center">

<img src="https://raw.githubusercontent.com/{username}/{username}/main/github-metrics.svg" width="100%" alt="GitHub Metrics"/>

<br/>

| Metric | Value |
|--------|-------|
| **Total Repositories** | {stats['repos']} Public |
| **Total Stars** | ⭐ {stats['stars']} |
| **Total Forks** | 🍴 {stats['forks']} |
| **Followers** | 👥 {stats['followers']} |
| **Following** | 👤 {stats['following']} |
| **Last Updated** | {now_utc} |

</div>

<!-- END_STATS -->"""

    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()

        pattern = r"<!-- START_STATS -->.*?<!-- END_STATS -->"
        if not re.search(pattern, content, flags=re.DOTALL):
            print("❌ Markers <!-- START_STATS --> / <!-- END_STATS --> not found in README.md")
            return False

        updated = re.sub(pattern, new_block, content, flags=re.DOTALL)

        with open("README.md", "w", encoding="utf-8") as f:
            f.write(updated)

        print(f"✅ README updated — stars:{stats['stars']} forks:{stats['forks']} followers:{stats['followers']}")
        return True

    except Exception as e:
        print(f"❌ Error writing README: {e}")
        return False


if __name__ == "__main__":
    username = os.getenv("GITHUB_USERNAME", "abhirajsingh1234")
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print("❌ GITHUB_TOKEN env var not set")
        raise SystemExit(1)

    print(f"🚀 Updating README for @{username} ...")
    success = update_readme(username, token)
    raise SystemExit(0 if success else 1)
