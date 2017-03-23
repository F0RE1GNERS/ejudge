# eJudge

### Installation:

The installation is very simple. (under good web condition of course)

1. clone the repository, and install Docker.
2. create local_config.py:
```python
HOST = '0.0.0.0'
PORT = 4999
DEBUG = False
TOKEN = 'naive'
```
3. run `sudo ./install_dependencies.sh`. (very slow, if you have run this in current version, skip this step)
4. have a cup of tea or coffee...
5. run `sudo ./install.sh`
6. `sudo docker run -it -p 4999:4999 ejudge/judge:v1`

And if nothing ridiculous pops out, done!

_Tips: You can use Ctrl + P + Q to have your terminal back. For advanced usage, learning a tutorial about docker is strongly recommended. :)_

### Token:

Token is required for all requests. Using `requests` library, this part comes naturally.

### Upload Data:

The data zipfile should be named `<pid>-<md5>.zip`, wrapping all data files and a compiled special judge (possibly) directly under the zipfile.

With token combined, this part looks like this:
```python
def add_listdir_to_file(source_dir, target_path):
    import zipfile
    f = zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED)
    for filename in os.listdir(source_dir):
        real_path = os.path.join(source_dir, filename)
        if os.path.isfile(real_path):
            f.write(real_path, arcname=filename)
    f.close()
```
```python
requests.post(url, data=f.read(), auth=('token', TOKEN)).json()
```

### Send Judge request
```python
requests.post(url, json=data, auth=('token', TOKEN)).json()
```
This part is quite simple. An example would look like this.
```json
{
  "id": 123, 
  "lang": "cpp",
  "code": "int main() { return 0; }",
  "settings": {
    "max_time": 1000,
    "max_sum_time": 10000,
    "max_memory": 256,
    "problem_id": "1000-shaaaaaa"
  },
  "judge": "ncmp"
}
```
Note that the problem id is not actually the problem id, it is `<pid>-<md5>`: same as above.

### Response

If something is wrong (data is missing or some part of request is missing), server will return:
```json
{
  "status": "reject"
}
```
Otherwise, `status` will be `received`.

Then, submission will be under processing. If `COMPILE_ERROR` occurred:
```json
{
  "id": 302,
  "message": "... In function 'int main()':\n/ju...",
  "verdict": 6,
  "status": "received"
}
```

Otherwise,
```json
{
  "id": 304, 
  "memory": 3052, 
  "status": "received", 
  "time": 588, 
  "verdict": 0,
  "detail": [{"count": 1, "memory": 2944, "time": 16, "verdict": 0}, {"count": 2, "memory": 2944, "time": 16, "verdict": 0}]
}
```

By the way, the verdict code list here:
```python
WRONG_ANSWER = -1
ACCEPTED = 0
CPU_TIME_LIMIT_EXCEEDED = 1
REAL_TIME_LIMIT_EXCEEDED = 2
MEMORY_LIMIT_EXCEEDED = 3
RUNTIME_ERROR = 4
SYSTEM_ERROR = 5
COMPILE_ERROR = 6
IDLENESS_LIMIT_EXCEEDED = 7
SUM_TIME_LIMIT_EXCEEDED = 8
```

Okay, that pretty much nails it! Good luck!

