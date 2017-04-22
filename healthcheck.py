import requests

from server import PORT


class HealthCheck:
    def __init__(self):
        self.url = 'http://localhost:%d' % (PORT)
        self.self_discovery_url = self.url + '/info'

    def server_info(self):
        res = requests.get(self.self_discovery_url, timeout=15).json()
        return res

    def heartbeat(self):
        try:
            data = self.server_info()
            # print(data)
            if data['status'] != 'ok':
                raise SystemError
        except Exception as e:
            print(e)
            return False
        return True


if __name__ == "__main__":
    if not HealthCheck().heartbeat():
        exit(1)
    exit(0)
