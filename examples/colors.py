from wiederverwendbar.functions.colors import Color

if __name__ == '__main__':
    color = Color(red=255, green=0, blue=0, alpha=0.5)
    color_str_rgb = color.as_rgb()
    color_str_rgba = color.as_rgba()
    color_str_hex = color.as_hex()
    color_str_hex_short = color.from_str("a0a")

    print("Color Class: ", color)
    print("Color RGB: ", color_str_rgb)
    print("Color RGBA: ", color_str_rgba)
    print("Color HEX: ", color_str_hex)
    print("Color HEX Short: ", color_str_hex_short)

    print()
