#define _GNU_SOURCE
#define _POSIX_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <sched.h>
#include <signal.h>
#include <pthread.h>
#include <wait.h>
#include <errno.h>
#include <unistd.h>
#include <string.h>

#include <sys/time.h>
#include <sys/resource.h>
#include <sys/types.h>

#include "runner.h"
#include "killer.h"
#include "child.h"
#include "logger.h"

int max(int a, int b) { return a > b ? a : b; }

int get_proc_info(pid_t pid, procinfo * pinfo)
{
    char szFileName [_POSIX_PATH_MAX], szStatStr [2048], *s, *t;
    FILE *fp;

    if (NULL == pinfo) {
        errno = EINVAL;
        return -1;
    }

    sprintf (szFileName, "/proc/%u/stat", (unsigned) pid);

    if (-1 == access (szFileName, R_OK)) {
        return (pinfo->pid = -1);
    }

    if ((fp = fopen (szFileName, "r")) == NULL) {
        return (pinfo->pid = -1);
    }

    if ((s = fgets (szStatStr, 2048, fp)) == NULL) {
        fclose (fp);
        return (pinfo->pid = -1);
    }

    // puts(szStatStr);

    /** pid **/
    sscanf (szStatStr, "%u", &(pinfo->pid));
    s = strchr (szStatStr, '(') + 1;
    t = strchr (szStatStr, ')');
    strncpy (pinfo->exName, s, t - s);
    pinfo->exName [t - s] = '\0';

    sscanf (t + 2, "%c %d %d %d %d %d %u %u %u %u %u %d %d %d %d %d %d %u %u %d %u %u %u %u %u %u %u %u %d %d %d %d %u",
      /*             1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33*/
      &(pinfo->state), &(pinfo->ppid), &(pinfo->pgrp), &(pinfo->session), &(pinfo->tty), &(pinfo->tpgid),
      &(pinfo->flags), &(pinfo->minflt), &(pinfo->cminflt), &(pinfo->majflt), &(pinfo->cmajflt), &(pinfo->utime),
      &(pinfo->stime), &(pinfo->cutime), &(pinfo->cstime), &(pinfo->counter), &(pinfo->priority), &(pinfo->timeout),
      &(pinfo->itrealvalue), &(pinfo->starttime), &(pinfo->vsize), &(pinfo->rss), &(pinfo->rlim), &(pinfo->startcode),
      &(pinfo->endcode), &(pinfo->startstack), &(pinfo->kstkesp), &(pinfo->kstkeip), &(pinfo->signal),
      &(pinfo->blocked), &(pinfo->sigignore), &(pinfo->sigcatch), &(pinfo->wchan));
    fclose (fp);
    return 0;
}

void init_result(struct result *_result) {
    _result->result = _result->error = SUCCESS;
    _result->cpu_time = _result->real_time = _result->signal = _result->exit_code = 0;
    _result->memory = 0;
}


void run(struct config *_config, struct result *_result) {
    // init log fp
    FILE *log_fp = log_open(_config->log_path);

    // init result
    init_result(_result);

    // check whether current user is root
    uid_t uid = getuid();
    if (uid != 0) {
        ERROR_EXIT(ROOT_REQUIRED);
    }

    // check args
    if ((_config->max_cpu_time < 1 && _config->max_cpu_time != UNLIMITED) ||
        (_config->max_real_time < 1 && _config->max_real_time != UNLIMITED) ||
        (_config->max_memory < 1 && _config->max_memory != UNLIMITED) ||
        (_config->max_process_number < 1 && _config->max_process_number != UNLIMITED) ||
        (_config->max_output_size < 1 && _config->max_output_size != UNLIMITED)) {
        ERROR_EXIT(INVALID_CONFIG);
    }

    // record current time
    struct timeval start, end;
    gettimeofday(&start, NULL);

    pid_t child_pid = fork();

    // pid < 0 shows clone failed
    if (child_pid < 0) {
        ERROR_EXIT(FORK_FAILED);
    }
    else if (child_pid == 0) {
        child_process(log_fp, _config);
    }
    else if (child_pid > 0){
        // create new thread to monitor process running time
        pthread_t tid = 0;
        if (_config->max_real_time != UNLIMITED) {
            struct timeout_killer_args killer_args;

            killer_args.timeout = _config->max_real_time;
            killer_args.pid = child_pid;
            if (pthread_create(&tid, NULL, timeout_killer, (void *) (&killer_args)) != 0) {
                kill_pid(child_pid);
                ERROR_EXIT(PTHREAD_FAILED);
            }
        }

        int status;
        struct rusage resource_usage;
        procinfo proc_info;

        // wait for child process to terminate
        // on success, returns the process ID of the child whose state has changed;
        // On error, -1 is returned.
        pid_t pid2;
        int memory_usage = 0, time_usage = 0;
        usleep(SLEEP_INTERVAL);
        do {
            get_proc_info(child_pid, &proc_info);
            time_usage = max(time_usage, proc_info.utime);
            memory_usage = max(memory_usage, proc_info.rss);

            usleep(SLEEP_INTERVAL);
            // wait for the child process to change state
            pid2 = wait4(child_pid, &status, WNOHANG, &resource_usage);
        } while (pid2 == 0);

        if (pid2 == -1) {
            kill_pid(child_pid);
            ERROR_EXIT(WAIT_FAILED);
        }

        // process exited, we may need to cancel timeout killer thread
        if (_config->max_real_time != UNLIMITED) {
            if (pthread_cancel(tid) != 0) {
                // todo logging
            };
        }

        _result->exit_code = WEXITSTATUS(status);
        _result->cpu_time = (int) (resource_usage.ru_utime.tv_sec * 1000 + resource_usage.ru_utime.tv_usec / 1000);
        // _result->cpu_time = time_usage * JIFFIES;
        _result->memory = memory_usage * PAGESIZE;
        // printf("%d %ld\n", _result->cpu_time, _result->memory);

        // get end time
        gettimeofday(&end, NULL);
        _result->real_time = (int) (end.tv_sec * 1000 + end.tv_usec / 1000 - start.tv_sec * 1000 - start.tv_usec / 1000);

        if (_result->exit_code != 0) {
            _result->result = RUNTIME_ERROR;
        }
        // if signaled
        if (WIFSIGNALED(status) != 0) {
            LOG_DEBUG(log_fp, "signal: %d", WTERMSIG(status));
            _result->signal = WTERMSIG(status);
            if (_result->signal == SIGSEGV) {
                if (_config->max_memory != UNLIMITED && _result->memory > _config->max_memory) {
                    _result->result = MEMORY_LIMIT_EXCEEDED;
                }
                else {
                    _result->result = RUNTIME_ERROR;
                }
            }
            else if(_result->signal == SIGUSR1) {
                _result->result = SYSTEM_ERROR;
            }
            else {
                _result->result = RUNTIME_ERROR;
            }
        }
        else {
            if (_config->max_memory != UNLIMITED && _result->memory > _config->max_memory) {
                _result->result = MEMORY_LIMIT_EXCEEDED;
            }
        }
        if (_config->max_real_time != UNLIMITED && _result->real_time > _config->max_real_time) {
            _result->result = REAL_TIME_LIMIT_EXCEEDED;
        }
        if (_config->max_cpu_time != UNLIMITED && _result->cpu_time > _config->max_cpu_time) {
            _result->result = CPU_TIME_LIMIT_EXCEEDED;
        }

        log_close(log_fp);
    }
}
