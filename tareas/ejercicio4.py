##Irvin Misael Mejia Hernandez


n = int(input())
m = int(input())
x = int(input())
mes = 0
total = n
print(mes, "%.6f" % total)
while total < x:
    total = total * 1.005 + m
    mes += 1
    print(mes, "%.6f" % total)

