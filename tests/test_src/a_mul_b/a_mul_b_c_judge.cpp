#include <bits/stdc++.h>
using namespace std;

int main(int argc, char **argv)
{
    ifstream fin(argv[1]);
    ofstream fout(argv[3]);
    long long a,b,c;
    fin >> a >> b;
    cin >> c;
    if (a * b != c)
        cout << "stop, wrong answer" << endl;
    else {
        cout << "continue, ok" << endl;
        fout << c << " " << c - 1 << endl;
        fout.close();
    }
    return 0;
}