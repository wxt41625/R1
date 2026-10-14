##Irvin Misael Mejia Hernandez


edades = list(map(int, input().split()))
unicas = list(set(edades))
unicas.sort(reverse=True)
resultado = list(map(str, unicas))
print(resultado)
