class A(object):
    def __init__(self):
        self.a = 1
    def x(self):
        return self.a

class B(A):
    def __init__(self):
        self.a = 2
    def x(self):
        return self.a
    def y(self):
        return super().x()

