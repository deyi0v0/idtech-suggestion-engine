from typing import Optional

# example to fetch installation links(top 1 priority: the software installation links. Consider feature: ...)
# you will get at least the hardware model name
# consider creating a mapping logic instead of direct map
DOC_MAPPING = {
    "VP6800": "https://idtech.com/support/documentation/vp6800-installation-guide/",
    "Universal SDK": "https://idtech.com/software/universal-sdk-docs/",
    "VP3300": "https://idtech.com/support/documentation/vp3300-user-manual/",
    "NEO 3": "https://idtech.com/support/documentation/neo3-docs/"
}

def fetch_installation_docs(product_name: str) -> Optional[str]:
    """
    Retrieve documentation or installation URLs for a given product.
    """
    return DOC_MAPPING.get(product_name, "https://idtech.com/support/")
