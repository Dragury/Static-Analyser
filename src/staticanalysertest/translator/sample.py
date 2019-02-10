# A basic python script for testing the translation

class MyClass:
    def method_a(self):
        print("Hello!")

    def method_b(self):
        self.method_a()
        print("Goodbye!")


def my_method(output):
    print(output)


if __name__ == "__main__":
    my_method("test")
    mc = MyClass()
    mc.method_b()
