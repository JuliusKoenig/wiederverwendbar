from wiederverwendbar.pydantic import Version

if __name__ == "__main__":
    version1_str = "1.0.0"
    version2_major = 1
    version2_minor = 0
    version2_patch = 1
    version3_str = "v1.0.0"


    version1 = Version(version1_str)
    version2 = Version(major=version2_major, minor=version2_minor, patch=version2_patch)
    version3 = Version(version3_str)

    print(int(version1))
    print(int(version2))
    print(int(version3))

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