import example2

def a(var1):
    def x():
        pass
    if var1 > 0:
        b()
        c()

def b():
    c()

def c():
    a(0)

x = 10
y = a(x)
x = 5
c(y)
example2.e(x)
b(x)