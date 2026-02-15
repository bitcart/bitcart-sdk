from datetime import date
from pathlib import Path
from urllib.request import urlretrieve

ASSETS = {
    "logo.svg": "https://bitcart.ai/logo.svg",
    "favicon.ico": "https://bitcart.ai/favicon.ico",
}


def on_config(config):
    config.copyright = f"Copyright &copy; 2019-{date.today().year} MrNaif2018"
    img_dir = Path(config.theme.custom_dir) / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    for filename, url in ASSETS.items():
        dest = img_dir / filename
        if not dest.exists():
            urlretrieve(url, dest)  # noqa: S310
