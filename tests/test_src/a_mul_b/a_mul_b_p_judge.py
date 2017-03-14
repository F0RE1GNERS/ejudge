import os, sys
newin = open(sys.argv[3], 'w')
oldin = open(sys.argv[1], 'r')
a, b = map(int, oldin.readline().split())
c = int(input())
if a * b != c:
    print('stop, wrong answer')
else:
    print('continue, ok')
    newin.write("%d %d\n" % (c, c - 1))