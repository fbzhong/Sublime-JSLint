import os
try:
  import thread
except ImportError:
  import threading
import subprocess
import functools
import sublime
import time

class AsyncProcess(object):
  def __init__(self, cmd, listener):
    self.cmd = cmd
    self.listener = listener
    self.proc = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("DEBUG_EXEC: " + str(self.cmd))

    if self.proc.stdout:
      self.stdoutThread = threading.Thread(target=self.read_stdout)
      self.stdoutThread.start()

    if self.proc.stderr:
      self.stderrThread = threading.Thread(target=self.read_stderr)
      self.stderrThread.start()

    self.pollThread = threading.Thread(target=self.poll)
    self.pollThread.start()

  def poll(self):
    while True:
      if self.proc.poll() != None:
        sublime.set_timeout(functools.partial(self.terminate), 0)
        break
      time.sleep(0.1)

  def read_stdout(self):
    while self.listener.is_running:
      data = os.read(self.proc.stdout.fileno(), 2**15)
      if data != b'':
        sublime.set_timeout(functools.partial(self.listener.append_data, self.proc, data), 0)

  def read_stderr(self):
    while self.listener.is_running:
      data = os.read(self.proc.stderr.fileno(), 2**15)
      if data != b'':
        sublime.set_timeout(functools.partial(self.listener.append_data, self.proc, data), 0)

  def terminate(self):
    sublime.set_timeout(functools.partial(self.listener.proc_terminated, self.proc), 0)
    self.listener.is_running = False
    self.pollThread.join()
    self.stdoutThread.join()
    self.proc.stdout.close()
    self.stderrThread.join()
    self.proc.stderr.close()

