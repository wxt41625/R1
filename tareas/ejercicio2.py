##Irvin Misael Mejia Hernandez


def hay_repetidos(vector):
    for i in range(len(vector)):
        for j in range(i + 1, len(vector)):
            if vector[i] == vector[j]:
                return 1
    return 0

n = int(input())
numeros = list(map(int, input().split()))
if hay_repetidos(numeros) == 1:
    print("YES")
else:
    print("NO")
