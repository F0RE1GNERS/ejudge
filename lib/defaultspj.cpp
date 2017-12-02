#include <iostream>
#include <cstring>
#include <algorithm>

using namespace std;

#define BUFFER_SIZE 100000
#define WA_EXIT_CODE 1
#define FAIL_EXIT_CODE 3

FILE *ouf, *ans, *ret;

inline bool isLineEnding(char c) {
    return c == '\r' || c == '\n';
}

inline bool isValidChar(char c) {
    return c && !isspace(c);
}

inline bool isCompressChar(char c) {
    return c && !isLineEnding(c);
}

class IO {
private:
    FILE* file;
    char ch, buf[BUFFER_SIZE], *p1, *p2;

public:
    int lineCount;

    explicit IO(FILE* f): file(f), ch(0), p1(buf), p2(buf), lineCount(1) {
        memset(buf, 0, sizeof buf);
    }

    inline int nextchar(char &r) {
        if (p1 == p2 && (p2 = (p1 = buf) + fread(buf, 1, BUFFER_SIZE, file), p1 == p2)) return 0;
        r = *p1++; if (r == '\n') lineCount++; return 1;
    }

    inline string compress() {
        char *lptr = p1, *rptr = p1;
        string ans; int i;
        for (i = 0; i < 16; ++i) {
            if (--lptr != buf - 1 && isCompressChar(*lptr))
                ans += *lptr;
            else break;
        }
        if (i == 16) ans += "...";
        reverse(ans.begin(), ans.end());

        for (i = 0; i < 15; ++i) {
            if (rptr++ != p2 && isCompressChar(*rptr))
                ans += *rptr;
            else break;
        }
        if (i == 15) ans += "...";
        return ans;
    }
};

void quit(int result) {
    fclose(ouf); fclose(ans); fclose(ret);
    exit(result);
}

void registerSpj(int argc, char* argv[]) {
    if (argc < 4 || argc > 6) {
        cout << "Program must be run with the following arguments: "
             << "<input-file> <output-file> <answer-file> [<report-file>]"
             << endl;
        exit(FAIL_EXIT_CODE);
    } else if (argc == 4) {
        ret = stdout;
    } if (argc == 5) {
        ret = fopen(argv[4], "w");
        if (ret == nullptr)
            exit(FAIL_EXIT_CODE);
    }

    ouf = fopen(argv[2], "r");
    if (ouf == nullptr) exit(FAIL_EXIT_CODE);
    ans = fopen(argv[3], "r");
    if (ans == nullptr) exit(FAIL_EXIT_CODE);
}

int main(int argc, char * argv[]) {
    registerSpj(argc, argv);

    IO outio(ouf), ansio(ans);

    char a, b;
    int ans_ok, ouf_ok;

    while (true) {
        ans_ok = ansio.nextchar(a);
        ouf_ok = outio.nextchar(b);

        if (ans_ok && ouf_ok) {
            if (a == b) {
                // not eof and equal (ok)
                continue;
            } else if (a == '\n') {
                // ans is at eol but ouf is not
                do {
                    if (isValidChar(b)) {
                        fprintf(ret, "wrong answer: unexpected character at the end of line %d\n", outio.lineCount);
                        quit(WA_EXIT_CODE);
                    }
                } while (outio.nextchar(b) && b != '\n');
            } else if (b == '\n') {
                // ouf is at eol but ans if not
                do {
                    if (isValidChar(a)) {
                        fprintf(ret, "wrong answer: character missing at the end of line %d\n", outio.lineCount - 1);
                        quit(WA_EXIT_CODE);
                    }
                } while (ansio.nextchar(a) && a != '\n');
            } else {
                // wrong answer
                fprintf(ret, "wrong answer: line %d differ - expected: '%s', found: '%s'\n", outio.lineCount,
                        ansio.compress().c_str(), outio.compress().c_str());
                quit(WA_EXIT_CODE);
            }
        } else {
            if (!ans_ok && !ouf_ok) {
                // both encountered eof
                break;
            } else if (!ans_ok) {
                // ouf is still not eof
                do {
                    if (isValidChar(b)) {
                        fprintf(ret, "wrong answer: unexpected output at eof\n");
                        quit(WA_EXIT_CODE);
                    }
                } while (outio.nextchar(b));
            } else {
                // ans is still not eof but ouf is eof now
                do {
                    if (isValidChar(a)) {
                        fprintf(ret, "wrong answer: output missing at eof\n");
                        quit(WA_EXIT_CODE);
                    }
                } while (ansio.nextchar(a));
            }
        }
    }

    fprintf(ret, "ok\n");
    return 0;
}