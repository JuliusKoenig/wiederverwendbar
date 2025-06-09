from wiederverwendbar.rich import RichConsoleSettings, RichConsole

if __name__ == '__main__':
    console_settings = RichConsoleSettings()
    console = RichConsole(settings=console_settings)
    console.print("Hello World!")

    console.card(("First Section",
                  "Line--------------------------------------------1\nLine--------------------------------------------2\nLine--------------------------------------------3"),
                 ("Second Section",
                  "Line--------------------------------------------1\nLine--------------------------------------------2\nLine--------------------------------------------3"),
                 "Line--------------------------------------------1\nLine--------------------------------------------2\nLine--------------------------------------------3",
                 padding_left=1,
                 padding_right=1,
                 max_width=40,
                 color="red",
                 header_color="green",
                 border_color="blue")
    print()
