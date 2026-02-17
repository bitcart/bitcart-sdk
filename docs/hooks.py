import gzip
import json
import re
from datetime import date
from pathlib import Path
from urllib.request import urlretrieve

ASSETS = {
    "logo.svg": "https://bitcart.ai/logo.svg",
    "favicon.ico": "https://bitcart.ai/favicon.ico",
}


def on_post_build(config):
    site_dir = Path(config.site_dir)
    pattern = re.compile(r'(href="[^"]*)\.html(?=["#?])')
    for html_file in site_dir.rglob("*.html"):
        content = html_file.read_text()
        updated = pattern.sub(r"\1", content)
        if content != updated:
            html_file.write_text(updated)
    sitemap = site_dir / "sitemap.xml"
    if sitemap.exists():
        content = sitemap.read_text()
        sitemap.write_text(content.replace(".html</loc>", "</loc>"))
        sitemap_gz = site_dir / "sitemap.xml.gz"
        if sitemap_gz.exists():
            sitemap_gz.write_bytes(gzip.compress(sitemap.read_bytes()))
    search_index = site_dir / "search" / "search_index.json"
    if search_index.exists():
        data = json.loads(search_index.read_text())
        for doc in data.get("docs", []):
            doc["location"] = re.sub(r"\.html(?=[#?]|$)", "", doc.get("location", ""))
        search_index.write_text(json.dumps(data, separators=(",", ":")))


def on_config(config):
    config.copyright = f"Copyright &copy; 2019-{date.today().year} MrNaif2018"
    img_dir = Path(config.theme.custom_dir) / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    for filename, url in ASSETS.items():
        dest = img_dir / filename
        if not dest.exists():
            urlretrieve(url, dest)  # noqa: S310
