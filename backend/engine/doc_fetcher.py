from typing import Optional
import requests
import re

BASE_URL = "https://idtechproducts.atlassian.net/wiki"
DOWNLOADS_PAGE_ID = "71697978" # all downloads are located here
HEADERS = {"User-Agent": "Mozilla/5.0"}


def find_product_page(model_name: str) -> Optional[str]:
    search_url = f"{BASE_URL}/rest/api/content/search"

    # try progressively looser CQL queries since they are not consistent across products
    cql_queries = [
        f'title="{model_name}: Home" AND space="KB" AND type=page',
        f'title="{model_name} Home" AND space="KB" AND type=page',
        f'title~"{model_name}" AND title~"Home" AND space="KB" AND type=page',
    ]

    for cql in cql_queries:
        params = {"cql": cql, "limit": 5}
        response = requests.get(search_url, params=params, headers=HEADERS)
        results = response.json().get("results", [])

        for r in results:
            # verify full model name is in title to avoid fuzzy match false positives
            if model_name.lower() in r["title"].lower():
                return r["id"]

    return None


def get_product_label(page_id: str, model_name: str) -> Optional[str]:
    page_url = f"{BASE_URL}/rest/api/content/{page_id}"
    response = requests.get(page_url, params={"expand": "body.storage"}, headers=HEADERS)
    body = response.json().get("body", {}).get("storage", {}).get("value", "")

    # try to extract from livesearch macro first
    match = re.search(
        r'ac:name="livesearch".*?ac:name="labels">([^<]+)</ac:parameter>',
        body,
        re.DOTALL
    )
    if match:
        labels = [l.strip() for l in match.group(1).split(",")]
        return labels[0]

    # fallback: derive label from model name- remove spaces + lowercase
    # e.g. MiniMag II -> minimagii
    fallback = re.sub(r'[^a-zA-Z0-9]', '', model_name).lower()
    print(f"No livesearch macro found, using derived label: {fallback}")
    return fallback


def fetch_installation_docs(model_name: str) -> Optional[list[dict]]:
    # find product home page
    page_id = find_product_page(model_name)
    if not page_id:
        print(f"No home page found for: {model_name}")
        return None

    print(f"Found page ID: {page_id}")

    # find product label
    product_label = get_product_label(page_id, model_name)
    if not product_label:
        print(f"No label found for: {model_name}")
        return None

    print(f"Found label: {product_label}")

    # search by product_label and manual label
    search_url = f"{BASE_URL}/rest/api/content/search"
    params = {
        "cql": f'type=attachment AND space="KB" AND label="{product_label}" AND label="manual"',
        "limit": 25,
        "expand": "metadata"
    }
    response = requests.get(search_url, params=params, headers=HEADERS)
    attachments = response.json().get("results", [])

    if not attachments:
        print(f"No manuals found for label: {product_label}")
        return None

    # format results
    docs = []
    for att in attachments:
        title = att.get("title", "")
        download = att.get("_links", {}).get("download", "")
        if download:
            docs.append({
                "title": title,
                "url": BASE_URL + download
            })

    return docs