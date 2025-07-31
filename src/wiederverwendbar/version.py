from pydantic import BaseModel, Field


class Version(BaseModel):
    major: int = Field(default=...,
                       title="Major version number",
                       description="Version number that indicates a significant change or update.",
                       ge=0)
    minor: int = Field(default=...,
                       title="Minor version number",
                       description="Version number that indicates a backward-compatible change or addition of functionality.",
                       ge=0)
    patch: int = Field(default=..., title="Patch version number",
                       description="Version number that indicates a backward-compatible bug fix or minor change.",
                       ge=0)

    def __str__(self) -> str:
        """
        Return a string representation of the version in the format 'vMAJOR.MINOR.PATCH'.

        :return: String representation of the version.
        """

        return f"v{self.major}.{self.minor}.{self.patch}"

    def __int__(self) -> int:
        """
        Convert the version to an integer representation.

        :return: Integer representation of the version, calculated as MAJOR * 10000 + MINOR * 100 + PATCH.
        """

        return self.major * 10000 + self.minor * 100 + self.patch

    @classmethod
    def from_string(cls, version_str: str) -> 'Version':
        """
        Create a Version instance from a version string in the format 'MAJOR.MINOR.PATCH'.

        :param version_str: Version string to parse.
        :return: Version instance.
        """

        parts = version_str.lstrip('v').split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version string: {version_str}")
        return cls(major=int(parts[0]),
                   minor=int(parts[1]),
                   patch=int(parts[2]))
