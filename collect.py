import subprocess, json, datetime, os, sys, shutil

def find_gh():
    env = os.environ.get("GH_BIN")
    if env and os.path.exists(env):
        return env
    found = shutil.which("gh")
    if found:
        return found
    # 兜底：本机已配置的 gh 路径
    fallback = r"C:\Users\tyy\.workbuddy\binaries\gh\bin\gh.exe"
    if os.path.exists(fallback):
        return fallback
    return "gh"

GH = find_gh()
OWNER = os.environ.get("GITHUB_OWNER") or (sys.argv[1] if len(sys.argv) > 1 else "truman-t3")

def gh(*args):
    r = subprocess.run([GH, *args], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout

def jget(raw):
    try:
        return json.loads(raw) if raw else None
    except Exception:
        return None

def fetch_star_history(name):
    """用 GitHub Stargazers API（带 starred_at）还原 Star 逐日累计历史。
    仅公开仓库可访问，无需额外 token；上限 1000 条防止超大仓库拖慢。"""
    raw = gh("api", f"repos/{OWNER}/{name}/stargazers",
             "--header", "Accept: application/vnd.github.star+json", "--paginate")
    if not raw:
        return []
    try:
        items = json.loads(raw)
    except Exception:
        return []
    if not isinstance(items, list):
        return []
    items = items[-1000:]
    counts = {}
    for it in items:
        sa = (it.get("starred_at") or "")[:10]
        if sa:
            counts[sa] = counts.get(sa, 0) + 1
    dates = sorted(counts.keys())
    out_dates, cum = [], 0
    for dd in dates:
        cum += counts[dd]
        out_dates.append({"date": dd, "cumulative": cum})
    return out_dates

repos_raw = gh("repo", "list", OWNER, "--limit", "100",
               "--json", "name,stargazerCount,forkCount,description,isPrivate,primaryLanguage,updatedAt,pushedAt,url")
repos = jget(repos_raw) or []

out = []
for repo in repos:
    name = repo["name"]
    entry = {
        "name": name,
        "description": repo.get("description"),
        "private": repo.get("isPrivate"),
        "language": (repo.get("primaryLanguage") or {}).get("name"),
        "stars": repo.get("stargazerCount"),
        "forks": repo.get("forkCount"),
        "url": repo.get("url"),
        "updatedAt": repo.get("updatedAt"),
        "pushedAt": repo.get("pushedAt"),
        "views": None, "viewUniques": None,
        "clones": None, "cloneUniques": None,
        "referrers": [], "paths": []
    }
    for kind, key in (("views", "views"), ("clones", "clones")):
        d = jget(gh("api", f"repos/{OWNER}/{name}/traffic/{kind}"))
        if d:
            if kind == "views":
                entry["views"], entry["viewUniques"] = d.get("count"), d.get("uniques")
            else:
                entry["clones"], entry["cloneUniques"] = d.get("count"), d.get("uniques")
    ref = jget(gh("api", f"repos/{OWNER}/{name}/traffic/popular/referrers"))
    if ref:
        entry["referrers"] = [{"referrer": x["referrer"], "count": x["count"], "uniques": x["uniques"]} for x in ref]
    pth = jget(gh("api", f"repos/{OWNER}/{name}/traffic/popular/paths"))
    if pth:
        entry["paths"] = [{"path": x["path"], "count": x["count"], "uniques": x["uniques"]} for x in pth[:10]]
    # Star 历史：仅公开仓库抓取，私有仓库无权限
    entry["starHistory"] = fetch_star_history(name) if not repo.get("isPrivate") else []
    out.append(entry)

data = {
    "generatedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "owner": OWNER,
    "repos": out
}
js = "window.DASHBOARD_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";"

# --- 历史快照：每日追加，同日期覆盖，用于趋势曲线 ---
today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
snap = {
    "date": today,
    "totals": {
        "stars": sum((r.get("stars") or 0) for r in out),
        "clones": sum((r.get("clones") or 0) for r in out),
        "views": sum((r.get("views") or 0) for r in out),
    },
    "repos": {r["name"]: {
        "stars": r.get("stars") or 0,
        "forks": r.get("forks") or 0,
        "views": r.get("views") or 0,
        "clones": r.get("clones") or 0,
        "cloneUniques": r.get("cloneUniques") or 0,
    } for r in out}
}
history = []
if os.path.exists("history.json"):
    try:
        with open("history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        history = []
history = [h for h in history if h.get("date") != today]
history.append(snap)
history.sort(key=lambda h: h["date"])
with open("history.json", "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

histJs = "window.DASHBOARD_HISTORY = " + json.dumps(history, ensure_ascii=False, indent=2) + ";"

# --- Star 历史（账号级累计）：合并各公开仓库的逐日增量 ---
repo_daily = {}
for r in out:
    prev = 0
    for pt in (r.get("starHistory") or []):
        inc = pt["cumulative"] - prev
        prev = pt["cumulative"]
        repo_daily[pt["date"]] = repo_daily.get(pt["date"], 0) + inc
star_total_pts, cum = [], 0
for dd in sorted(repo_daily.keys()):
    cum += repo_daily[dd]
    star_total_pts.append({"date": dd, "cumulative": cum})
star_history = {
    "total": star_total_pts,
    "repos": {r["name"]: (r.get("starHistory") or []) for r in out}
}
starJs = "window.STAR_HISTORY = " + json.dumps(star_history, ensure_ascii=False, indent=2) + ";"

with open("data.js", "w", encoding="utf-8") as f:
    f.write(js + "\n" + histJs + "\n" + starJs)

# 内嵌数据 + 历史到 index.html，生成不依赖外部 data.js 的单文件看板
with open("index.template.html", "r", encoding="utf-8") as f:
    tpl = f.read()
html = (tpl.replace("/*__DASHBOARD_DATA__*/", js)
            .replace("/*__DASHBOARD_HISTORY__*/", histJs)
            .replace("/*__STAR_HISTORY__*/", starJs))
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("collected", len(out), "repos -> index.html (self-contained) + history.json points:", len(history),
      "| star-history points:", len(star_total_pts))
