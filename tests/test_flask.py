import requests
import json
from socketIO_client import SocketIO, LoggingNamespace

from config.config import DATA_BASE, Verdict
from core.case import Case
from tests.test_base import TestBase


class FlaskTest(TestBase):

    def setUp(self):
        self.workspace = '/tmp/flask'
        self.url_base = 'http://localhost:5000'
        self.token = ('ejudge', 'naive') # Token has to be reset to do this test
        super(FlaskTest, self).setUp()

    def test_upload_success(self):
        fingerprint = 'test_%s' % self.rand_str()
        result = requests.post(self.url_base + '/upload/case/%s/input' % fingerprint, data=b'123123',
                               auth=self.token).json()
        self.assertEqual(result['status'], 'received')
        result = requests.post(self.url_base + '/upload/case/%s/output' % fingerprint, data=b'456456',
                               auth=self.token).json()
        self.assertEqual(result['status'], 'received')
        case = Case(fingerprint)
        case.check_validity()
        with open(case.input_file, 'r') as f1:
            self.assertEqual(f1.read(), '123123')
        with open(case.output_file, 'r') as f2:
            self.assertEqual(f2.read(), '456456')

    def test_upload_fail(self):
        fingerprint = 'test_%s' % self.rand_str()
        result = requests.post(self.url_base + '/upload/case/%s/input' % fingerprint, data=b'123123',
                               auth=('123', '345')).json()
        self.assertEqual(result['status'], 'reject')

    def test_aplusb_judge(self):
        checker_fingerprint = self.rand_str(True)
        case_fingerprints = [self.rand_str(True) for _ in range(31)]
        checker_dict = dict(fingerprint=checker_fingerprint, lang='cc11', code=open('./submission/ncmp.cpp').read())
        response = requests.post(self.url_base + "/upload/checker/%s" % checker_fingerprint,
                                 json=json.dumps(checker_dict), auth=self.token)
        self.assertEqual(response.json()['status'], 'received')

        for i, fingerprint in enumerate(case_fingerprints):
            response = requests.post(self.url_base + '/upload/case/%s/input' % fingerprint,
                                     data=open('./data/aplusb/ex_input%d.txt' % (i + 1), 'rb').read(),
                                     auth=self.token)
            self.assertEqual(response.json()['status'], 'received')
            requests.post(self.url_base + '/upload/case/%s/output' % fingerprint,
                          data=open('./data/aplusb/ex_output%d.txt' % (i + 1), 'rb').read(),
                          auth=self.token)
        judge_upload = dict(fingerprint=self.rand_str(True), lang='cc11', code=open('./submission/aplusb.cc11').read(),
                            cases=case_fingerprints, max_time=1, max_memory=128, checker=checker_fingerprint,
                            )
        news_length = 0
        result = None

        def callback(*args):
            nonlocal news_length, result, self
            body = args[0]
            if body.get('verdict') != Verdict.JUDGING.value:
                result = body
            else:
                detail = body.get('detail')
                self.assertEqual(news_length + 1, len(detail))
                news_length = len(detail)

        with SocketIO('localhost', 5000, LoggingNamespace) as socketIO:
            socketIO.emit('judge', judge_upload)
            socketIO.on('judge_reply', callback)
            while not result:
                socketIO.wait(seconds=1)
        self.assertEqual(result['verdict'], 0)
