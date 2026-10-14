##Irvin Misael Mejia Hernandez


for a in range(1, 5):
    for b in range(1, 5):
        if b != a:
            for c in range(1, 5):
                if c != a and c != b:
                    for d in range(1, 5):
                        if d != a and d != b and d != c:
                            print(a, b, c, d)
