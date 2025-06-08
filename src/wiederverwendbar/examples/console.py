from wiederverwendbar.console import ConsoleSettings, Console

if __name__ == '__main__':
    console_settings = ConsoleSettings()
    console = Console(settings=console_settings)
    console.print("Hello World!")
    print()
