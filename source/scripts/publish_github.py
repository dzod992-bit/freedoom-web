"""Publish dist/ to this project's free public GitHub Pages repository.

Uses the existing Git Credential Manager login. Credentials stay in memory.
Never force-pushes or changes an unrelated repository.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
OWNER = "dzod992-bit"
REPO = "freedoom-web"
URL = f"https://{OWNER}.github.io/{REPO}/"
REMOTE = f"https://github.com/{OWNER}/{REPO}.git"
CHECKOUT = ROOT / ".publish" / REPO
os.environ["GIT_TERMINAL_PROMPT"] = "0"
os.environ["GCM_INTERACTIVE"] = "Never"


def git(*args, capture=False):
    return subprocess.run(
        ["git", "-C", str(CHECKOUT), *args], check=True,
        text=True, capture_output=capture,
    ).stdout


def main():
    for name in ("index.html", "doom.js", "doom.wasm", "doom.data", ".nojekyll"):
        if not (ROOT / "dist" / name).is_file():
            raise SystemExit(f"Missing dist/{name}. Run scripts/build.ps1 first.")
    response = subprocess.run(
        ["git", "credential", "fill"],
        input=f"protocol=https\nhost=github.com\nusername={OWNER}\n\n",
        text=True, capture_output=True, check=True,
    )
    credential = dict(line.split("=", 1) for line in response.stdout.splitlines() if "=" in line)
    headers = {
        "Authorization": "Bearer " + credential["password"],
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Freedoom-Web-Publish",
    }

    def api(path, method="GET", data=None):
        body = json.dumps(data).encode() if data is not None else None
        request = urllib.request.Request("https://api.github.com" + path,
                                         data=body, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=60) as result:
            payload = result.read()
            return json.loads(payload) if payload else None

    if api("/user")["login"].lower() != OWNER.lower():
        raise SystemExit("The GitHub login does not match the deployment owner.")
    repo_path = f"/repos/{OWNER}/{REPO}"
    try:
        repository = api(repo_path)
        if not (CHECKOUT / ".git").is_dir():
            raise SystemExit("The repository already exists without our local checkout; refusing to overwrite it.")
        if repository["private"]:
            raise SystemExit("Expected a public repository. Its visibility was not changed.")
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        repository = api("/user/repos", "POST", {
            "name": REPO,
            "description": "Chocolate Doom + Freedoom 2 in the browser, compiled to WebAssembly. GPL source and BSD content included.",
            "homepage": URL, "private": False,
            "has_issues": True, "has_projects": False, "has_wiki": False,
        })
        print("Created public repository:", repository["html_url"], flush=True)

    CHECKOUT.mkdir(parents=True, exist_ok=True)
    if not (CHECKOUT / ".git").is_dir():
        git("init", "-b", "main")
        git("remote", "add", "origin", REMOTE)
    if git("remote", "get-url", "origin", capture=True).strip() != REMOTE:
        raise SystemExit("Unexpected deployment remote. Nothing was uploaded.")
    git("config", "user.name", OWNER)
    git("config", "user.email", f"{api('/user')['id']}+{OWNER}@users.noreply.github.com")
    git("config", "core.autocrlf", "false")
    shutil.copytree(ROOT / "dist", CHECKOUT, dirs_exist_ok=True)
    (CHECKOUT / "README.md").write_text(
        "# Freedoom in your browser\n\n"
        f"**[Play online]({URL})** — desktop Chrome or Edge recommended.\n\n"
        "Chocolate Doom compiled with Emscripten, SDL2, SDL2_mixer and Asyncify. "
        "Includes Freedoom 2 v0.13.0. Saves are stored locally in IndexedDB.\n\n"
        "WASD: move; mouse: turn; click/Ctrl: fire; Space: use; Shift: run; "
        "F2: save; F3: load; Esc: menu/release mouse.\n\n"
        "The initial download is approximately 31 MB. No account or installation is needed.\n\n"
        "## Source and licenses\n\n"
        "[Corresponding source](source/) includes the engine archive, patches, "
        "build scripts and browser integration. See [build instructions](source/README.md).\n\n"
        "Chocolate Doom and engine modifications: GPL-2.0-or-later. "
        "Freedoom: BSD-3-Clause. Third-party notices are in [licenses/](licenses/).\n\n"
        "## Hosting\n\n"
        "GitHub Pages serves the main branch root. `.nojekyll` keeps compiled assets intact. "
        "This repository contains only the static release and its corresponding source.\n",
        encoding="utf-8",
    )
    git("add", "--all")
    changed = subprocess.run(["git", "-C", str(CHECKOUT), "diff", "--cached", "--quiet"])
    if changed.returncode == 1:
        git("commit", "-m", "Publish Chocolate Doom WebAssembly with Freedoom and persistent saves")
    elif changed.returncode:
        raise SystemExit("Could not inspect staged files.")
    git("push", "-u", "origin", "main")
    try:
        pages = api(repo_path + "/pages")
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        pages = api(repo_path + "/pages", "POST", {
            "build_type": "legacy", "source": {"branch": "main", "path": "/"},
        })
    deployment = {"url": pages["html_url"], "repository": repository["html_url"],
                  "commit": git("rev-parse", "HEAD", capture=True).strip(),
                  "status": pages.get("status")}
    (ROOT / ".publish" / "deployment.json").write_text(json.dumps(deployment, indent=2), encoding="utf-8")
    print(json.dumps(deployment, indent=2), flush=True)


if __name__ == "__main__":
    main()
