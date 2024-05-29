from wiederverwendbar.singleton import Singleton


class A(metaclass=Singleton, order=3):
    def __init__(self):
        print("A created")

    def __del__(self):
        print("A deleted")


class B(metaclass=Singleton, order=2):
    def __init__(self):
        print("B created")

    def __del__(self):
        print("B deleted")


class C(metaclass=Singleton, order=1):
    def __init__(self):
        print("C created")

    def __del__(self):
        print("C deleted")


def init():
    A(init=True)
    B(init=True)
    C(init=True)
    print("init")


def main():
    a = A()
    b = B()
    c = C()

    print("main")


if __name__ == '__main__':
    Singleton.delete_ordered_on_exit = True
    init()
    main()