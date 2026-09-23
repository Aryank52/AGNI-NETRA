#!/usr/bin/env python3
"""
AGNI-NETRA — Pre-Commit Secret Guard
Strictly prevents committing environment files, private keys, credentials,
real DATABASE_URLs, and sensitive API tokens to the Git repository.

In accordance with AGNI-NETRA Security Governance:
"Environment files containing real secrets are LOCAL-ONLY and must NEVER be committed or pushed to GitHub."
"""

import sys
import re
import subprocess
import os

BLOCKED_FILE_PATTERNS = [
    (re.compile(r"(^|/)\.env(\..+)?$", re.IGNORECASE), "Environment file (.env / .env.*)"),
    (re.compile(r".*\.(pem|key|p12|pfx|secrets)$", re.IGNORECASE), "Private key / certificate file"),
    (re.compile(r"(^|/)(credentials|service_account.*)\.json$", re.IGNORECASE), "Credential / Service account file"),
]

ALLOWED_FILE_PATTERNS = [
    re.compile(r".*\.env\.example$", re.IGNORECASE),
]

SECRET_CONTENT_PATTERNS = [
    (
        re.compile(r"^\+[^\n]*-----BEGIN (?:[A-Z0-9_-]+\s+)?PRIVATE KEY-----", re.MULTILINE),
        "Cryptographic Private Key block"
    ),
    (
        re.compile(r"^\+[^\n]*\b(AIzaSy[0-9A-Za-z_-]{33})\b", re.MULTILINE),
        "Google Cloud / Maps API Key format"
    ),
    (
        re.compile(r"^\+[^\n]*\b(ghp_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{50,})\b", re.MULTILINE),
        "GitHub Personal Access Token"
    ),
    (
        re.compile(r"^\+[^\n]*\b(sbp_[0-9a-f]{40})\b", re.MULTILINE),
        "Supabase Access Token"
    ),
    (
        re.compile(r"^\+[^\n]*\bDATABASE_URL\s*=\s*['\"]?(?:postgres|postgresql)(?:\+[a-z0-9]+)?://([^:]+):([^@]+)@", re.MULTILINE | re.IGNORECASE),
        "DATABASE_URL with embedded password credentials"
    ),
]

SAFE_PASSWORD_PLACEHOLDERS = {
    "password", "your_postgres_password", "your_password", "user:password",
    "postgres", "db_password", "replace_with_password", "<db_password>",
    "********", "****", "change_in_production"
}


def get_staged_files():
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True
        )
        return [f.strip() for f in res.stdout.splitlines() if f.strip()]
    except Exception as e:
        print(f"[SECURITY GUARD ERROR] Failed to inspect git staging: {e}", file=sys.stderr)
        return []


def get_staged_diff():
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "-U0"],
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout
    except Exception as e:
        print(f"[SECURITY GUARD ERROR] Failed to read git diff: {e}", file=sys.stderr)
        return ""


def check_staged_filenames(staged_files):
    violations = []
    for filepath in staged_files:
        norm_path = filepath.replace("\\", "/")
        is_allowed = any(p.match(norm_path) for p in ALLOWED_FILE_PATTERNS)
        if is_allowed:
            continue

        for pattern, desc in BLOCKED_FILE_PATTERNS:
            if pattern.search(norm_path):
                violations.append((filepath, desc))
                break
    return violations


def check_staged_content(diff_text):
    violations = []
    current_file = "Unknown file"

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
            continue

        # Skip example files or tests checking sanitizers
        if current_file.endswith(".env.example") or "test_phase13_production_hardening" in current_file:
            continue

        for pattern, desc in SECRET_CONTENT_PATTERNS:
            match = pattern.search(line)
            if match:
                # If DATABASE_URL, check whether password is just a dummy template placeholder
                if "DATABASE_URL" in desc:
                    pwd = match.group(2).strip().lower()
                    if pwd in SAFE_PASSWORD_PLACEHOLDERS:
                        continue
                violations.append((current_file, desc))
                break
    return violations


def main():
    staged_files = get_staged_files()
    if not staged_files:
        sys.exit(0)

    filename_violations = check_staged_filenames(staged_files)
    diff_text = get_staged_diff()
    content_violations = check_staged_content(diff_text)

    all_violations = filename_violations + content_violations

    if all_violations:
        print("\n" + "=" * 78, file=sys.stderr)
        print("  [BLOCKED BY AGNI-NETRA SECRET GUARD]", file=sys.stderr)
        print("  Commit aborted: Sensitive environment or credential files detected!", file=sys.stderr)
        print("=" * 78, file=sys.stderr)
        print("\nPolicy Invariant:", file=sys.stderr)
        print("  'Environment files containing real secrets are LOCAL-ONLY and must NEVER", file=sys.stderr)
        print("   be committed or pushed to GitHub.'\n", file=sys.stderr)
        print("Detected Violations (Values Redacted for Safety):", file=sys.stderr)

        for filename, reason in all_violations:
            print(f"  • File:   {filename}", file=sys.stderr)
            print(f"    Reason: {reason}", file=sys.stderr)

        print("\nRecommended Remediation:", file=sys.stderr)
        print("  1. Remove secret files from Git staging:", file=sys.stderr)
        print("     git reset HEAD <filename>", file=sys.stderr)
        print("  2. If the file was previously tracked, untrack without deleting locally:", file=sys.stderr)
        print("     git rm --cached <filename>", file=sys.stderr)
        print("  3. Verify .gitignore covers the file before retrying commit.", file=sys.stderr)
        print("=" * 78 + "\n", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
