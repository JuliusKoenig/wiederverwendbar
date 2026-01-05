from wiederverwendbar.branding.settings import BrandingSettings

import examples


class MyAppSettings(BrandingSettings, module=examples):
    attr1: str
    attr2: str


def main():
    app_settings = MyAppSettings(attr1="value1", attr2="value2")
    print(app_settings.model_dump_json(indent=2))
    print(app_settings.version.minor)


if __name__ == '__main__':
    main()
