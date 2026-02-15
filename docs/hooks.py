from datetime import date


def on_config(config):
    config.copyright = f"Copyright &copy; 2019-{date.today().year} MrNaif2018"
