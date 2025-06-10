from wiederverwendbar.branding.settings import BrandingSettings

if __name__ == '__main__':
    branding_settings = BrandingSettings()
    print(branding_settings.model_dump_json(indent=2))
