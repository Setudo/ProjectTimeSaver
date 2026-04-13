"""Utilities to download a GitHub repository into a local folder.

Main entrypoint: download_repo(repo_url, destination_folder) -> (bool, message)

Behavior:
- Normalize GitHub URLs (https, git@, .git suffixes).
- Prefer `git clone --depth 1` when `git` is available.
- Fall back to downloading the repository ZIP archive and extracting.
- Enforce MAX_DOWNLOAD_BYTES (abort and clean up if exceeded).
- Return (success: bool, message: str).
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple

try:
    import requests
except Exception:  # pragma: no cover - requests may not be installed in dev env
    requests = None

# 200 MiB default maximum download size
MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024

GITHUB_API_BASE = "https://api.github.com/repos"


def _normalize_github_url(url: str) -> Tuple[str, str, str]:
    """Normalize various GitHub URL styles and return (owner, repo, https_url).

    Raises ValueError on invalid format.
    """
    if not url or not isinstance(url, str):
        raise ValueError("Empty repository URL")

    url = url.strip()

    # Handle scp-like git@github.com:owner/repo.git
    scp_match = re.match(r"^(?:git@|ssh://git@)github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$", url)
    if scp_match:
        owner = scp_match.group("owner")
        repo = scp_match.group("repo")
        https = f"https://github.com/{owner}/{repo}"
        return owner, repo, https

    # Normalize http(s) urls
    m = re.match(r"^https?://(www\.)?github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$", url)
    if m:
        owner = m.group("owner")
        repo = m.group("repo")
        https = f"https://github.com/{owner}/{repo}"
        return owner, repo, https

    # Maybe user passed owner/repo
    m2 = re.match(r"^(?P<owner>[^/]+)/(?P<repo>[^/]+)$", url)
    if m2:
        owner = m2.group("owner")
        repo = m2.group("repo")
        https = f"https://github.com/{owner}/{repo}"
        return owner, repo, https

    raise ValueError("Invalid GitHub repository URL or format")


def _is_git_available() -> bool:
    try:
        subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False


def _compute_folder_size(path: Path) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                fp = os.path.join(root, f)
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def _get_github_metadata(owner: str, repo: str) -> Optional[dict]:
    if requests is None:
        return None
    try:
        resp = requests.get(f"{GITHUB_API_BASE}/{owner}/{repo}", timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None
    return None


def _safe_extract_zip(zip_path: Path, extract_to: Path) -> None:
    """Extract zip to extract_to safely (prevent zip-slip)."""
    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.infolist():
            member_name = member.filename
            # Skip absolute paths
            if os.path.isabs(member_name):
                raise ValueError("Archive contains absolute paths")
            # Resolve path and ensure it's inside extract_to
            dest_path = (extract_to / member_name).resolve()
            if not str(dest_path).startswith(str(extract_to.resolve())):
                raise ValueError("Archive contains files outside extraction directory")
        z.extractall(path=extract_to)


def _attempt_clone(repo_url: str, dest: Path, max_bytes: int) -> Tuple[bool, str]:
    dest_temp = Path(tempfile.mkdtemp(prefix="repo_clone_"))
    try:
        # First try with partial clone filter to reduce download if supported
        cmd = ["git", "clone", "--depth", "1", "--filter=blob:none", repo_url, str(dest_temp)]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=600)
        except subprocess.CalledProcessError:
            # Retry without filter (older git)
            cmd = ["git", "clone", "--depth", "1", repo_url, str(dest_temp)]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=600)

        size = _compute_folder_size(dest_temp)
        if size > max_bytes:
            shutil.rmtree(dest_temp, ignore_errors=True)
            return False, f"Repository exceeds size limit ({size / (1024 * 1024):.1f} MiB > {max_bytes / (1024 * 1024):.1f} MiB)"

        # Move into final destination (ensure parent exists)
        dest_parent = dest.parent
        dest_parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            shutil.rmtree(dest, ignore_errors=True)
        shutil.move(str(dest_temp), str(dest))
        return True, "Cloned repository successfully"
    except subprocess.CalledProcessError as e:
        shutil.rmtree(dest_temp, ignore_errors=True)
        stderr = getattr(e, "stderr", None)
        if stderr:
            try:
                stderr = stderr.decode(errors="ignore")
            except Exception:
                stderr = str(stderr)
        return False, f"git clone failed: {stderr or str(e)}"
    except Exception as e:
        shutil.rmtree(dest_temp, ignore_errors=True)
        return False, f"Clone failed: {str(e)}"


def _download_zip_and_extract(owner: str, repo: str, branch: str, dest: Path, max_bytes: int, progress_callback=None) -> Tuple[bool, str]:
    if requests is None:
        return False, "requests module is not available to download zip archive"

    zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
    try:
        head = requests.head(zip_url, allow_redirects=True, timeout=15)
        if head.status_code >= 400:
            return False, f"Could not find archive at {zip_url} (status {head.status_code})"
        content_length = head.headers.get("Content-Length")
        total_bytes = 0
        if content_length is not None:
            try:
                cl = int(content_length)
                total_bytes = cl
                if cl > max_bytes:
                    return False, f"Archive content-length {cl} bytes exceeds limit {max_bytes} bytes"
            except Exception:
                pass

        # Stream download into temp file and enforce max_bytes
        temp_file = Path(tempfile.mkstemp(prefix="repo_zip_", suffix=".zip")[1])
        total = 0
        with requests.get(zip_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(temp_file, "wb") as fh:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        total += len(chunk)
                        if progress_callback and total_bytes > 0:
                            progress_callback(total, total_bytes)
                        if total > max_bytes:
                            fh.close()
                            temp_file.unlink(missing_ok=True)
                            return False, f"Download exceeded size limit ({total} > {max_bytes} bytes)"
                        fh.write(chunk)

        # Extract safely into a temp dir then move
        extract_temp = Path(tempfile.mkdtemp(prefix="repo_unzip_"))
        try:
            _safe_extract_zip(temp_file, extract_temp)
            # After extraction, compute size
            size = _compute_folder_size(extract_temp)
            if size > max_bytes:
                shutil.rmtree(extract_temp, ignore_errors=True)
                temp_file.unlink(missing_ok=True)
                return False, f"Extracted repository exceeds size limit ({size} bytes)"

            # Many GitHub zips extract into a single top-level folder like repo-branch/
            entries = list(extract_temp.iterdir())
            final_src = extract_temp
            if len(entries) == 1 and entries[0].is_dir():
                final_src = entries[0]

            dest_parent = dest.parent
            dest_parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                shutil.rmtree(dest, ignore_errors=True)
            shutil.move(str(final_src), str(dest))
            # Cleanup
            try:
                if extract_temp.exists():
                    shutil.rmtree(extract_temp, ignore_errors=True)
            except Exception:
                pass
            temp_file.unlink(missing_ok=True)
            return True, "Downloaded and extracted repository successfully"
        except Exception as e:
            shutil.rmtree(extract_temp, ignore_errors=True)
            temp_file.unlink(missing_ok=True)
            return False, f"Failed to extract archive: {str(e)}"
    except Exception as e:
        return False, f"Failed to download archive: {str(e)}"


def download_repo(repo_url: str, destination_folder: str, max_bytes: int = MAX_DOWNLOAD_BYTES, progress_callback=None) -> Tuple[bool, str]:
    """Download a GitHub repository into `destination_folder`.

    Returns (success, message).
    progress_callback: optional callable(bytes_downloaded, total_bytes) for progress reporting.
    """
    try:
        owner, repo, https_url = _normalize_github_url(repo_url)
    except ValueError as e:
        return False, f"Invalid GitHub URL: {str(e)}"

    dest = Path(destination_folder)
    # Ensure destination parent exists
    dest_parent = dest.parent
    dest_parent.mkdir(parents=True, exist_ok=True)

    # If repo already exists at destination, treat as success
    if dest.exists() and any(dest.iterdir()):
        return True, "Repository already present"

    # Try to get metadata (optional)
    metadata = _get_github_metadata(owner, repo)
    default_branch = None
    if metadata:
        default_branch = metadata.get("default_branch")
        api_size_kb = metadata.get("size")
        if isinstance(api_size_kb, (int, float)):
            # API reports size in KB (approx). Convert to bytes for heuristic check.
            api_bytes = int(api_size_kb * 1024)
            if api_bytes > max_bytes:
                return False, f"Repository reported size {api_bytes} bytes exceeds allowed limit {max_bytes} bytes"

    # Prefer git if available
    if _is_git_available():
        ok, msg = _attempt_clone(https_url + ".git", dest, max_bytes)
        if ok:
            return True, msg
        # if clone failed, attempt zip fallback

    # Zip fallback
    branch = default_branch or "main"
    ok, msg = _download_zip_and_extract(owner, repo, branch, dest, max_bytes, progress_callback)
    if ok:
        return True, msg

    # If zip fallback failed and default branch was main, try master
    if branch == "main":
        ok2, msg2 = _download_zip_and_extract(owner, repo, "master", dest, max_bytes, progress_callback)
        if ok2:
            return True, msg2

    # If we reached here, everything failed; return last message
    return False, msg


if __name__ == "__main__":
    # Quick CLI for manual testing
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("repo")
    p.add_argument("dest")
    args = p.parse_args()
    ok, message = download_repo(args.repo, args.dest)
    print(ok, message)