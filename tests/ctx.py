class SingletonContextManager:
    context_managers = {}

    def __new__(cls, *args, **kwargs):
        # override __exit__ method to call __post_exit__ method
        __exit__ = getattr(cls, "__exit__", None)

        def __singleton_exit__(*a):
            if __exit__ is not None:
                __exit__(*a)

            # remove context manager from context_managers
            if self in cls.context_managers:
                del cls.context_managers[self]

        if __exit__.__name__ != "__singleton_exit__":
            cls.__exit__ = __singleton_exit__

        # create a new instance of the class
        self = super().__new__(cls)

        # set '_already_created' attribute to
        self._already_created = False

        # check if a context manager with attributes args and kwargs already exists
        init_attrs = {"args": args, "kwargs": kwargs}
        for context_manager, context_manager_init_attrs in cls.context_managers.items():
            if context_manager_init_attrs == init_attrs:
                self_dict = {}
                for key, value in context_manager.__dict__.items():
                    self_dict[key] = value
                self.__dict__ = self_dict
                self._already_created = True
                return self

        cls.context_managers[self] = init_attrs

        return self

    @property
    def already_created(self) -> bool:
        return self._already_created


class Connection:
    def __init__(self, name: str):
        self.name = name
        self.is_open = False

    def open(self):
        print(f"Opening connection {self.name}")
        self.is_open = True

    def close(self):
        print(f"Closing connection {self.name}")
        self.is_open = False


class ConnectionContextManager(SingletonContextManager):
    def __init__(self, name: str, array: list):
        if self.already_created:
            return
        self.connection = Connection(name)

    def __enter__(self):
        if self.already_created:
            return self.connection

        self.connection.open()
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.already_created:
            return

        self.connection.close()

def main():
    with ConnectionContextManager("test", ["qwe"]) as connection1:
        with ConnectionContextManager("test", ["qwe"]) as connection2:
            connection_id1 = id(connection1)
            connection_id2 = id(connection2)
            same = connection1 is connection2
            print()
        print()
    print()



if __name__ == '__main__':
    main()
    print()
