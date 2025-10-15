from wiederverwendbar.pydantic import Version

if __name__ == "__main__":
    version1_str = "1.0.0a1"
    version2_major = 1
    version2_minor = 0
    version2_patch = 0
    version2_prerelease_type = "release_candidate"
    version2_prerelease_number = 1
    version3_str = "v1.0.0a1"


    version1 = Version(version1_str)
    version2 = Version(major=version2_major,
                       minor=version2_minor,
                       patch=version2_patch,
                       prerelease_type=version2_prerelease_type,
                       prerelease_number=version2_prerelease_number)
    version3 = Version(version3_str)

    version1_int = int(version1)
    version2_int = int(version2)
    version3_int = int(version3)
    print(version1_int)
    print(version2_int)
    print(version3_int)

    print(version1 == version2)  # False
    print(version1 != version2)  # True
    print(version1 == version3)  # True
    print(version1 != version3)  # False
    print(version1 < version2)  # True
    print(version1 <= version2)  # True
    print(version1 > version2)  # False
    print(version1 >= version2)  # False

    print(version1)
    print(version2)
    print(version3.major)