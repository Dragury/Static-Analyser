# A basic python script for testing the translation
import argparse
import toml
from sys import stderr, stdin, stdout


class MyClass:
    _attribute_A = 1
    _attribute_B: int = 2

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


def my_method_2(test=4, yes: str = "yes!") -> None:
    print("hello!")


def my_method_3() -> None:
    test = 1
    if test == 1:
        print("test is 1!")
    for i in (1, 2, 3):
        for j in (1, 2, 3):
            print("hello!")
            print("goodbye!!")
    while True:
        print(test)


if __name__ == "__main__":
    my_method("test")
    mc = MyClass()
    mc.method_b()
