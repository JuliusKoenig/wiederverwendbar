from wiederverwendbar.branding.settings import BrandingSettings

if __name__ == '__main__':
    branding_settings = BrandingSettings()
    branding_settings_dict = branding_settings.model_dump()

    print()
