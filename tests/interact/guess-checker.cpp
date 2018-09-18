#include "testlib.h"
#include <stdio.h>

int main(int argc, char * argv[])
{
    setName("compare less than 32");
    registerTestlibCmd(argc, argv);
    int pa = ouf.readInt();

    if (pa >= 32)
        quitf(_wa, "out of expectation");

    quitf(_ok, "correct");
}