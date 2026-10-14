##Irvin Misael Mejia Hernandez


n, m = map(int, input().split())
alturas = [0] * m
for i in range(n):
    fila = input().split()
    for j in range(m):
        if fila[j] == "1":
            alturas[j] += 1
print(*alturas)
