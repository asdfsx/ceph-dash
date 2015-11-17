#!/usr/bin/env python
#! -*- coding: utf-8 -*-

import traceback
import subprocess

class CommandExecutor(object):
    def __init__(self):
        pass

    def executeCmd(self, cmd):
        try:
            return subprocess.check_output(cmd, shell=True)
        except Exception as exc:
            return exc
