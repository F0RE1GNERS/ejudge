! Enter your code here. Read input from STDIN. Print output to STDOUT
FUNCTION solve_me_first(val1, val2)
    INTEGER :: solve_me_first
    INTEGER :: val1
    INTEGER :: val2
    solve_me_first = val1 + val2
    RETURN
END FUNCTION

PROGRAM main
    IMPLICIT NONE

    INTEGER :: val1
    INTEGER :: val2
    INTEGER :: solve_me_first

    READ(*,*) val1
    READ(*,*) val2
    WRITE(*,'(i0)') solve_me_first(val1, val2)
END PROGRAM main
