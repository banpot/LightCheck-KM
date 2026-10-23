"""Programmatic KPIs of the knowledge repository (used on the poster/slides).
Usage: python tools/repo_stats.py  -> prints and writes tools/repo_stats.json"""
import json
import os
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def files(ext, sub=""):
    out = []
    for d, _, fs in os.walk(os.path.join(ROOT, sub)):
        if any(p in d for p in (".git", "node_modules", "__pycache__")):
            continue
        out += [os.path.join(d, f) for f in fs if f.lower().endswith(ext)]
    return out


def loc(paths):
    n = 0
    for p in paths:
        with open(p, encoding="utf-8", errors="ignore") as fh:
            n += sum(1 for line in fh if line.strip())
    return n


def git(*args):
    try:
        return subprocess.check_output(["git", "-C", ROOT, *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


stats = {
    "markdown_docs": len(files(".md")),
    "firmware_loc": loc(files(".ino", "firmware")),
    "python_tools": len(files(".py")),
    "python_loc": loc(files(".py")),
    "stl_files": len([p for p in files(".stl") if "proxies" not in p]),
    "figures_png": len(files(".png")),
    "commits": int(git("rev-list", "--count", "HEAD") or 0),
    "contributors": len(set(git("log", "--format=%an").splitlines())) if git("log", "-1") else 0,
}
with open(os.path.join(ROOT, "tools", "repo_stats.json"), "w") as fh:
    json.dump(stats, fh, indent=2)
print(json.dumps(stats, indent=2))
