from wiederverwendbar.console import ConsoleSettings, Console

if __name__ == '__main__':
    console_settings = ConsoleSettings()
    console = Console(settings=console_settings)
    console.print("Hello World!")

    console.card(("First Section", "Line--------------------------------------------1\nLine--------------------------------------------2\nLine--------------------------------------------3"),
                 ("Second Section", "Line--------------------------------------------1\nLine--------------------------------------------2\nLine--------------------------------------------3"),
                 "Line--------------------------------------------1\nLine--------------------------------------------2\nLine--------------------------------------------3",
                 padding_left=1,
                 padding_right=1,
                 max_width=40)

    print()
