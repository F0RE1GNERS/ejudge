#include <bits/stdc++.h>
using namespace std;

const int maxl = 300000;
const int maxn = 12;

const int x = 89;
int n, len[maxn];
char s[maxn][maxl];
unsigned long long h[maxn][maxl], xp[maxl], Hash[maxn][maxl];

int check(int length) {
    int i = 0, forcheck = 1;
    while (forcheck <= n) {
        int hash_length = len[forcheck] - length + 1;
        for (int j = 0; j < hash_length; ++j)
            Hash[forcheck][j] = h[forcheck][j] - h[forcheck][j+length] * xp[length];
        sort(Hash[forcheck], Hash[forcheck] + hash_length);
        int ok = 0;
        for (; i < len[0] - length + 1; ++i) {
            unsigned long long tt = h[0][i] - h[0][i+length] * xp[length];
            if (binary_search(Hash[forcheck], Hash[forcheck] + hash_length, tt)) {
                ok = 1;
                i += length;
                break;
            }
        }
        if (ok) forcheck++;
        else return 0;
    }
    return 1;
}

int main() {
    //freopen("test.in", "r", stdin);
    scanf("%s", s[0]);
    scanf("%d", &n);
    for (int i = 1; i <= n; ++i)
        scanf("%s", s[i]);

    for (int i = 0; i <= n; ++i)
        len[i] = strlen(s[i]);

    xp[0] = 1;
    for (int i = 1; i < maxl; ++i)
        xp[i] = xp[i-1] * x;

    for (int i = 0; i <= n; ++i) {
        h[i][len[i]] = 0;
        for (int j = len[i] - 1; j >= 0; --j)
            h[i][j] = h[i][j + 1] * x + s[i][j] - 'a';
    }

    int left = 1, right = 2e9;
    for (int i = 1; i <= n; ++i)
        right = min(right, len[i]);

    if (!check(1)) {
        printf("-1\n");
        return 0;
    }
    while (left < right) {
        int mid = (left + right + 1) / 2;
        if (check(mid)) left = mid;
        else right = mid - 1;
    }
    printf("%d\n", left);

    return 0;
}