
from importlib import reload
import os
import sys
import io
import threading
import asyncio
import functools
import inspect
import typing
import subprocess

subprocess.call(['javac','-J-Duser.language=en','-cp','test','test/jbridge/Example.java','test/jbridge/JbridgeStubJ.java'])

import PursuerJavaBridgeGen

jbg=PursuerJavaBridgeGen.JavaClassStub()
jbg.loadByPath('./test/jbridge/JbridgeStubJ.java')
PursuerJavaBridgeGen.generateToDir([jbg],'./test')

cc=os.environ['CC']
subprocess.call([cc,'-shared','-o','jbridge_stub.dll','test/jbridge_stub.c','test/jbridge_test.c'])

subprocess.call(['java','-Duser.language=en','-cp','./test','jbridge/Example'])