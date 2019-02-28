# A basic python script for testing the translation

class MyClass:
    def method_a(self):
        print("Hello!")

    def method_b(self):
        self.method_a()
        print("Goodbye!")


def my_decorator(func):
    def inner(out):
        print("I'm decorated!")
        func(out)

    return inner


@my_decorator
def my_method(output) -> None:
    print(output)


if __name__ == "__main__":
    my_method("test")
    mc = MyClass()
    mc.method_b()
