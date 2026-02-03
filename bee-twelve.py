import datetime
import hashlib
import hmac
import json
import os
import sys
import urllib.request

URL = "https://b12.io/apply/submission"


def iso8601_utc_ms() -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    s = now.isoformat(timespec="milliseconds")
    return s.replace("+00:00", "Z")


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def main() -> None:
    # All applicant-specific data from env
    name = required_env("BEE_TWELVE_APPLICANT_NAME")
    email = required_env("BEE_TWELVE_APPLICANT_EMAIL")
    resume_link = required_env("BEE_TWELVE_RESUME_LINK")
    repo_link = required_env("BEE_TWELVE_REPOSITORY_LINK")

    # Signing secret from env (but you’ll set it to hello-there-from-b12 in CI)
    signing_secret = required_env("BEE_TWELVE_SIGNING_SECRET")

    # Derive action_run_link from GitHub Actions env vars
    repo = required_env("GITHUB_REPOSITORY")
    run_id = required_env("GITHUB_RUN_ID")
    action_run_link = f"https://github.com/{repo}/actions/runs/{run_id}"

    payload = {
        "action_run_link": action_run_link,
        "email": email,
        "name": name,
        "repository_link": repo_link,
        "resume_link": resume_link,
        "timestamp": iso8601_utc_ms(),
    }

    body_str = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    body = body_str.encode("utf-8")

    digest = hmac.new(signing_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-Signature-256": f"sha256={digest}",
    }

    req = urllib.request.Request(URL, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        resp_json = json.loads(resp.read().decode("utf-8"))

    # Print just the receipt
    print(resp_json["receipt"])


if __name__ == "__main__":
    main()