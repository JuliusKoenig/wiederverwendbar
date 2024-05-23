from wiederverwendbar.singleton import Singleton


class A(metaclass=Singleton):
    def __init__(self):
        print("A created")

    def __del__(self):
        print("A deleted")


class B(metaclass=Singleton):
    def __init__(self):
        print("B created")

    def __del__(self):
        print("B deleted")


class C(metaclass=Singleton):
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


def end():
    Singleton.delete_all()
    print("end")


if __name__ == '__main__':
    init()
    main()
    end()

    print()
