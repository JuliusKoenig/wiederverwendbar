from wiederverwendbar.post_init import PostInit

class MyParentClass(PostInit):
    def __init__(self, parent_attr: str):
        super().__init__()

        self.parent_attr = parent_attr

        print(f"Parent attribute: {parent_attr}")

    def __post_init__(self):
        print(f"Parent post init attribute: {self.parent_attr}")


class MyClass(MyParentClass):
    def __init__(self, my_attr: str, parent_attr: str):
        super().__init__(parent_attr=parent_attr)

        self.my_attr = my_attr

        print(f"My attribute: {my_attr}")

    def __post_init__(self):
        super().__post_init__()
        print(f"My post init attribute: {self.my_attr}")


if __name__ == '__main__':
    my_class = MyClass(my_attr="My attribute", parent_attr="Parent attribute")