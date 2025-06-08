from wiederverwendbar.rich import RichConsoleSettings, RichConsole

if __name__ == '__main__':
    console_settings = RichConsoleSettings()
    console = RichConsole(settings=console_settings)
    print()
