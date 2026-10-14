##Irvin Misael Mejia Hernandez


b1, b2, b3 = map(int, input().split())
n = int(input())
numeros = list(map(int, input().split()))
resultado = []
for numero in numeros:
    if numero != b1 and numero != b2 and numero != b3:
        resultado.append(numero)
print(*resultado)
