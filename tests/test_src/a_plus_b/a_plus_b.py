while True:
    try:
        s = input()
    except EOFError:
        break
    a, b = map(int, s.split())
    print(a + b)