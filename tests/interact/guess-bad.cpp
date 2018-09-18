#include <bits/stdc++.h>

using namespace std;


string str;
int l = -1000000000;
int r =  1000000000;

int main()
{
    while(1) {
        int mid = (l + r) / 2;
        cout << mid;
        fflush(stdout);
        cin >> str;
        if (str == "equal")
            break;
        else if (str == "small")
            l = mid + 1;
        else
            r = mid;
    }
    return 0;
}
