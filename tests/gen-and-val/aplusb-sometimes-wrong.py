import sys

a, b = map(int, input().split())
if a % 2 == 0:
    print(a + b + 1)
else:
    print(a + b)
sys.stdout.flush()