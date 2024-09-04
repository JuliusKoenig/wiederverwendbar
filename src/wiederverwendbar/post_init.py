class PostInit:
    def __new__(cls, *args, **kwargs):
        # get __init__ method
        __init__ = cls.__init__

        # wrap __init__ method
        def post_init(self, *a, **kw):
            __init__(self, *a, **kw)

            # check if __post_init__ method exists
            if hasattr(self, "__post_init__"):
                self.__post_init__()

        cls.__init__ = post_init

        return super().__new__(cls)

    def __post_init__(self):
        ...
