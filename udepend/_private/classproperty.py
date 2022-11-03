class classproperty:
    """
    Decorator that converts a method with a single cls argument into a property getter
    that can be accessed directly from the class.
    """

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, instance, cls):
        return self.fget(cls)

    def getter(self, method):
        self.fget = method
        return self
