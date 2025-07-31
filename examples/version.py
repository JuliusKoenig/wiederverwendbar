from wiederverwendbar.version import Version

if __name__ == '__main__':
    version1 = Version(major=1, minor=0, patch=0)
    print(f"version1: {version1} -> {int(version1)}")
    version2 = Version(major=1, minor=0, patch=1)
    print(f"version2: {version2} -> {int(version2)}")
