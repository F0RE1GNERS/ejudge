import websockets
import asyncio
from os import path
import json

from config.config import DATA_BASE, PROJECT_BASE, Verdict
from core.case import Case
from tests.test_base import TestBase


class SocketTest(TestBase):

    def setUp(self):
        self.workspace = '/tmp/socket'
        self.url_base = 'ws://localhost:5001'
        self.username = 'ejudge'
        self.password = 'naive'
        self.extra_headers = {'username': self.username, 'password': self.password}
        with open(path.join(PROJECT_BASE, 'config/token.yaml'), 'w') as f:
            f.write('username: %s\npassword: %s\n' % (self.username, self.password))
        super(SocketTest, self).setUp()

    def generate_random_text(self):
        real_random = "aaab" + self.rand_str()
        random_text_path = '/tmp/test_unicode_random_text.txt'
        with open(random_text_path, 'w') as f:
            for i in range(10000):
                f.write(real_random)
            f.write('这是中文hahaha')
        return random_text_path

    def test_connect(self):
        async def _connect(self):
            async with websockets.connect(self.url_base, extra_headers=self.extra_headers.items()) as websocket:
                message = await websocket.recv()
                self.assertEqual(json.loads(message).get('message'), 'Authorization granted. Goodbye...')
        asyncio.get_event_loop().run_until_complete(_connect(self))

    async def _upload_case(self, case_path, fingerprint, subcase='in'):
        self.extra_headers.update(fingerprint=fingerprint, subcase=subcase, length=path.getsize(case_path))
        async with websockets.connect(self.url_base + '/upload/case',
                                      extra_headers=self.extra_headers.items()) as websocket:
            with open(case_path, 'rb') as f:
                while True:
                    d = f.read(4096)
                    if d:
                        await websocket.send(d)
                    else:
                        break
            response = await websocket.recv()
            self.assertEqual(json.loads(response).get('status'), 'received', msg=json.loads(response).get('message'))
            atext = self.output_content(case_path)
            btext = self.output_content(path.join(DATA_BASE, fingerprint, subcase))
            self.assertEqual(atext, btext)

    async def _send_json_and_receive(self, path, d):
        async with websockets.connect(self.url_base + path, extra_headers=self.extra_headers.items()) as websocket:
            await websocket.send(json.dumps(d))
            response = "{}"
            while True:
                try:
                    response = await websocket.recv()
                    print(response)
                except websockets.ConnectionClosed:
                    break
            return json.loads(response)

    def test_upload_case(self):
        random_text_path = self.generate_random_text()
        fingerprint = self.rand_str(True)
        asyncio.get_event_loop().run_until_complete(self._upload_case(random_text_path, fingerprint))

    def test_judge_aplusb(self):
        async def verify_result(self, data):
            response = await self._send_json_and_receive('/judge', data)
            self.assertEqual(response['verdict'], Verdict.ACCEPTED)

        checker_fingerprint = self.rand_str(True)
        checker_dict = dict(fingerprint=checker_fingerprint, lang='cc11', code=open('./submission/ncmp.cpp').read())
        asyncio.get_event_loop().run_until_complete(self._send_json_and_receive("/upload/checker", checker_dict))
        case_fingerprints = [self.rand_str(True) for _ in range(31)]
        for i in range(31):
            asyncio.get_event_loop().run_until_complete(
                self._upload_case('./data/aplusb/ex_input%d.txt' % (i + 1), case_fingerprints[i], 'in'))
            asyncio.get_event_loop().run_until_complete(
                self._upload_case('./data/aplusb/ex_output%d.txt' % (i + 1), case_fingerprints[i], 'out'))
        judge_upload = dict(fingerprint=self.rand_str(True), lang='cc11', code=open('./submission/aplusb.cc11').read(),
                            cases=case_fingerprints, max_time=1, max_memory=128, checker=checker_fingerprint,
                            )
        asyncio.get_event_loop().run_until_complete(verify_result(self, judge_upload))