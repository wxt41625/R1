##Irvin Misael Mejia Hernandez


a, b = map(int, input().split())
multiplos = []
for i in range(a, b + 1, a):
    multiplos.append(i)
print(*multiplos)
