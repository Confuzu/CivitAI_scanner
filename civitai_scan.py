import csv
import getpass
import os
import re
import sys
import urllib.parse

import requests
from tqdm import tqdm

BASE_URL = "https://civitai.com/api/v1/models"
ALLOWED_HOSTS = {"civitai.com", "www.civitai.com"}
REQUEST_TIMEOUT = 30
CSV_FIELDS = [
    "Author", "Item Name", "Model Version Name", "Item Type",
    "Base Model", "File Name", "Download URL", "Model Image",
    "Model Version URL",
]


def get_token() -> str:
    """Token priority: CIVITAI_API_TOKEN env var → interactive prompt."""
    token = os.environ.get("CIVITAI_API_TOKEN", "")
    if token:
        return token
    try:
        token = getpass.getpass("CivitAI API token (Enter to skip): ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(1)
    return token


def sanitize_username(username: str) -> str:
    """Strip dangerous characters so the username is safe as a filename."""
    safe = re.sub(r'[^\w\-]', '_', username).strip('_.')
    if not safe:
        raise ValueError(f"Username {username!r} cannot be used as a filename")
    return safe[:64]


def validate_next_page(url: str | None) -> str | None:
    """Ensure the pagination URL is a CivitAI HTTPS API endpoint."""
    if not url:
        return None
    try:
        p = urllib.parse.urlparse(url)
        if p.scheme != "https":
            print(f"  WARN  rejected non-HTTPS nextPage URL")
            return None
        if p.netloc not in ALLOWED_HOSTS:
            print(f"  WARN  rejected nextPage URL with unexpected host: {p.netloc}")
            return None
        if not p.path.startswith("/api/"):
            print(f"  WARN  rejected nextPage URL with unexpected path: {p.path}")
            return None
        return url
    except Exception:
        return None


def get_json(url: str, session: requests.Session) -> dict:
    """Fetch a URL and return parsed JSON. Raises on HTTP or network errors."""
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def extract_rows(data: dict, username: str) -> list[dict]:
    """Extract one CSV row per file from a single page of API results."""
    rows = []
    for item in data.get("items", []):
        if not isinstance(item, dict):
            continue

        item_id   = item.get("id", "")
        item_name = item.get("name", "")
        item_type = item.get("type") or ""

        for version in item.get("modelVersions", []):
            if not isinstance(version, dict):
                continue

            version_id   = version.get("id", "")
            version_name = version.get("name", "")
            base_model   = version.get("baseModel") or ""
            images       = version.get("images", [])
            image_url    = images[0].get("url", "") if images else ""

            model_url   = f"https://civitai.com/models/{item_id}"
            version_url = f"https://civitai.com/models/{item_id}?modelVersionId={version_id}"

            for file in version.get("files", []):
                if not isinstance(file, dict):
                    continue
                rows.append({
                    "Author":               username,
                    "Item Name":            item_name,
                    "Model Version Name":   version_name,
                    "Item Type":            item_type,
                    "Base Model":           base_model,
                    "File Name":            file.get("name", ""),
                    "Download URL":         file.get("downloadUrl", ""),
                    "Model Image":          image_url,
                    "Model Version URL":    version_url,
                })
    return rows


def build_statistics(rows: list[dict]) -> dict[str, int]:
    """Count rows by 'ItemType-BaseModel' combination."""
    stats: dict[str, int] = {}
    for row in rows:
        key = f"{row['Item Type']}-{row['Base Model']}"
        stats[key] = stats.get(key, 0) + 1
    return stats


def write_csv(rows: list[dict], path: str) -> None:
    """Write rows to a CSV file atomically (temp file + rename)."""
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def main() -> None:
    try:
        username = input("Enter CivitAI username: ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(1)

    if not username:
        print("No username provided.")
        sys.exit(1)

    try:
        safe_username = sanitize_username(username)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    token = get_token()

    session = requests.Session()
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    # Build initial URL
    params = urllib.parse.urlencode({"username": username, "nsfw": "true"})
    next_url: str | None = f"{BASE_URL}?{params}"

    all_rows: list[dict] = []
    page = 0
    total_items = None

    pbar = tqdm(desc="Fetching pages", unit="page")
    try:
        while next_url:
            try:
                data = get_json(next_url, session)
            except requests.HTTPError as e:
                status = e.response.status_code if e.response is not None else "?"
                print(f"\nHTTP {status} error — stopping.")
                break
            except requests.RequestException as e:
                print(f"\nNetwork error: {e} — stopping.")
                break

            # Show total on first page
            if page == 0:
                total_items = data.get("metadata", {}).get("totalItems")
                if total_items:
                    print(f"  Total items reported by API: {total_items}")

            page += 1
            pbar.update(1)

            rows = extract_rows(data, username)
            all_rows.extend(rows)

            next_url = validate_next_page(data.get("metadata", {}).get("nextPage"))
    finally:
        pbar.close()

    if not all_rows:
        print("No data retrieved.")
        sys.exit(0)

    output_path = os.path.join(os.getcwd(), f"{safe_username}_output.csv")
    write_csv(all_rows, output_path)
    print(f"\nWrote {len(all_rows)} rows to {output_path}")

    stats = build_statistics(all_rows)
    print("\nModel statistics (Type-BaseModel):")
    for key, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {count:>6}  {key}")


if __name__ == "__main__":
    main()
