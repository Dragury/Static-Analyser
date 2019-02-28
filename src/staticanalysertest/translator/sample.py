# A basic python script for testing the translation

class MyClass:
    def method_a(self):
        print("Hello!")

    def method_b(self):
        self.method_a()
        print("Goodbye!")

class AnotherClass(MyClass):
    def method_c(self, banana):
        print(banana)

def my_decorator(func):
    def inner(out):
        print("I'm decorated!")
        func(out)

    return inner


@my_decorator
def my_method(output) -> None:
    print(output)

def my_method_2() -> None:
    print("hello!")

def my_method_3() -> None:
    print("hello!")

if __name__ == "__main__":
    my_method("test")
    mc = MyClass()
    mc.method_b()
