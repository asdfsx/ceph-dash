#!/usr/env/bin python
#! -*- coding: utf-8 -*-

from . import base

class rados(base.CommandExecutor):
    def __init__(self):
        self.prefix = "rados "
        self.cmdmap = {"ls":"ls --pool %s --format json",
                       }


    def generate(self, cmdname, **para):
        if cmdname == "ls":
            if 'pool' in para :
                return True, self.prefix + self.cmdmap[cmdname] % (para['pool'],)
            else:
                return False, "need 'pool' in parameters"
        else:
            return True, self.prefix + self.cmdmap[cmdname]

    def execute(self, cmdname, **para):
        isSuccess, result = self.generate(cmdname, **para)
        if isSuccess:
            return True, self.executeCmd(result)
        else:
            return False, result
       
    def __call__(self, cmdname, **para):
        return self.execute(cmdname, **para)

