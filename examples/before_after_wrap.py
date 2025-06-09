from wiederverwendbar.before_after_wrap import WrappedClass, wrap


class BaseClass(metaclass=WrappedClass):
    def before_cls_test1(self, __ba_before_result__):
        print("before_cls_test1")

    @wrap(before=before_cls_test1, after="after_cls_test1")
    def cls_test1(self, __ba_before_result__):
        print("cls_test1")

    def after_cls_test1(self, __ba_result__):
        print("after_cls_test1")

    def before_cls_test2(self):
        print("before_cls_test2")

    @wrap(before=before_cls_test2, after="after_cls_test2")
    def cls_test2(self):
        print("cls_test2")

    def after_cls_test2(self):
        print("after_cls_test2")


class ChildClass(BaseClass):
    def before_cls_test1A(self):
        print("before_cls_test1A")

    @wrap(before=before_cls_test1A, after="after_cls_test1A", include_base=False)
    def cls_test1(self, __ba_before_result__):
        super().cls_test1(__ba_use__=False)
        print("cls_test1A")

    def after_cls_test1A(self):
        print("after_cls_test1A")

    def before_cls_test3(self):
        print("before_cls_test3")

    @wrap(before=before_cls_test3, after="after_cls_test3")
    def cls_test3(self):
        print("cls_test3")

    def after_cls_test3(self):
        print("after_cls_test3")


def before_test1(*_, **__):
    print("before_test1")


@wrap(before=before_test1, after="after_test1")
def test1(arg1: str):
    print(f"test1 -> {arg1}")


def after_test1(*_, **__):
    print("after_test1")


if __name__ == "__main__":
    base_class = BaseClass()
    base_class.cls_test1()
    base_class.cls_test2()

    child_class = ChildClass()
    child_class.cls_test1()
    child_class.cls_test2()
    child_class.cls_test3()

    test1("qwe")


