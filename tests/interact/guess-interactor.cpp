#include "testlib.h"
#include <iostream>

using namespace std;

int main(int argc, char* argv[])
{
    setName("Interactor Guessing");
    registerInteraction(argc, argv);

    // reads number of queries from test (input) file
    int guess = inf.readInt();
    int t, ans = 0;
    do {
        t = ouf.readInt();
        if (t < guess) cout << "small" << endl;
        else if (t > guess) cout << "big" << endl;
        else cout << "equal" << endl;
        ans++;
    } while (t != guess);
    tout << ans << endl;

    // just message
    quitf(_ok, "%d", ans);
}