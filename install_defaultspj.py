from core.judge import TrustedSubmission

program = TrustedSubmission('defaultspj', open('lib/defaultspj.cpp').read(), 'cpp', permanent=True)
program.compile(30)