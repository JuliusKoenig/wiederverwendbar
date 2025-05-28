from typing import Optional

from pydantic import BaseModel, Field


class Color(BaseModel):
    red: int = Field(default=0, ge=0, le=255, title="Red", description="The red value of the color.")
    green: int = Field(default=0, ge=0, le=255, title="Green", description="The green value of the color.")
    blue: int = Field(default=0, ge=0, le=255, title="Blue", description="The blue value of the color.")
    alpha: float = Field(default=1.0, ge=0, le=1, title="Alpha", description="The alpha value of the color.")

    @classmethod
    def from_str(cls, color_str: str) -> "Color":
        """
        Parse a color from a string.
        Examples:
        rgb(255, 0, 0) -> Color(red=255, green=0, blue=0, alpha=1.0)
        rgba(255, 0, 0, 0.5) -> Color(red=255, green=0, blue=0, alpha=0.5)
        #ff0000 -> Color(red=255, green=0, blue=0, alpha=1.0)
        ff0000 -> Color(red=255, green=0, blue=0, alpha=1.0)
        f0f -> Color(red=255, green=0, blue=255, alpha=1.0)
        255, 0, 0 -> Color(red=255, green=0, blue=0, alpha=1.0)
        255, 0, 0, 0.5 -> Color(red=255, green=0, blue=0, alpha=0.5)

        :param color_str: The color string.
        :return: Returns the Color object.
        """

        color_str = color_str.strip()
        color_str = color_str.lower()

        if color_str.startswith("rgb(") and color_str.endswith(")"):
            color_str = color_str[4:-1]
        elif color_str.startswith("rgba(") and color_str.endswith(")"):
            color_str = color_str[5:-1]
        elif color_str.startswith("#"):
            color_str = color_str[1:]

        color_dict = {}
        if "," in color_str:
            color_str_split = color_str.split(",")
            color_dict["red"] = int(color_str_split.pop(0).strip())
            if len(color_str_split) > 0:
                color_dict["green"] = int(color_str_split.pop(0).strip())
            if len(color_str_split) > 0:
                color_dict["blue"] = int(color_str_split.pop(0).strip())
            if len(color_str_split) > 0:
                color_dict["alpha"] = float(color_str_split.pop(0).strip())
            if len(color_str_split) > 0:
                raise ValueError(f"Invalid color string '{color_str}'.")
        elif 3 <= len(color_str) <= 6:
            if len(color_str) < 6:
                red_hex = color_str[0:1] + color_str[0:1]
                green_hex = color_str[1:2] + color_str[1:2]
                blue_hex = color_str[2:3] + color_str[2:3]
            else:
                red_hex = color_str[0:2]
                green_hex = color_str[2:4]
                blue_hex = color_str[4:6]
            color_dict["red"] = int(red_hex, 16)
            color_dict["green"] = int(green_hex, 16)
            color_dict["blue"] = int(blue_hex, 16)
        else:
            raise ValueError(f"Invalid color string '{color_str}'.")

        return cls(**color_dict)

    def as_rgb(self,
               red_overwrite: Optional[int] = None,
               green_overwrite: Optional[int] = None,
               blue_overwrite: Optional[int] = None) -> str:
        """
        Parse the color object to a rgb string.

        :param red_overwrite: Overwrite the red value.
        :param green_overwrite: Overwrite the green value.
        :param blue_overwrite: Overwrite the blue value.
        :return: Returns the rgb string.
        """

        red = red_overwrite if red_overwrite is not None else self.red
        green = green_overwrite if green_overwrite is not None else self.green
        blue = blue_overwrite if blue_overwrite is not None else self.blue

        # parse to str
        color_str = f"rgb({red}, {green}, {blue})"

        # validate
        _ = self.from_str(color_str=color_str)

        return color_str

    def as_rgba(self,
                red_overwrite: Optional[int] = None,
                green_overwrite: Optional[int] = None,
                blue_overwrite: Optional[int] = None,
                alpha_overwrite: Optional[float] = None) -> str:
        """
        Parse the color object to a rgba string.

        :param red_overwrite: Overwrite the red value.
        :param green_overwrite: Overwrite the green value.
        :param blue_overwrite: Overwrite the blue value.
        :param alpha_overwrite: Overwrite the alpha value.
        :return: Returns the rgba string.
        """

        red = red_overwrite if red_overwrite is not None else self.red
        green = green_overwrite if green_overwrite is not None else self.green
        blue = blue_overwrite if blue_overwrite is not None else self.blue
        alpha = alpha_overwrite if alpha_overwrite is not None else self.alpha

        # parse to str
        color_str = f"rgba({red}, {green}, {blue}, {alpha})"

        # validate
        _ = self.from_str(color_str=color_str)

        return color_str

    def as_hex(self,
               red_overwrite: Optional[int] = None,
               green_overwrite: Optional[int] = None,
               blue_overwrite: Optional[int] = None,
               include_rhombus: bool = True) -> str:
        """
        Parse the color object to a hex string.

        :param red_overwrite: Overwrite the red value.
        :param green_overwrite: Overwrite the green value.
        :param blue_overwrite: Overwrite the blue value.
        :param include_rhombus: Include the rhombus in the hex string.
        :return: Returns the hex string.
        """

        red = red_overwrite if red_overwrite is not None else self.red
        green = green_overwrite if green_overwrite is not None else self.green
        blue = blue_overwrite if blue_overwrite is not None else self.blue

        # parse to str
        color_str = "#" if include_rhombus else ""
        color_str += f"{red:02x}{green:02x}{blue:02x}"

        # validate
        _ = self.from_str(color_str=color_str)

        return color_str
