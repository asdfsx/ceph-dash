#!/usr/env/bin python
#! -*- coding: utf-8 -*-

from . import base

class rbd(base.CommandExecutor):
    def __init__(self):
        self.prefix = "rbd "
        self.cmdmap = {"ls":"ls --pool %s --format json",
                       "showmapped":"showmapped --format json",
                       "info":"info --pool %s --image %s --format json",
                       "snapls":"snap ls --pool %s --image %s --format json"
                       }


    def generate(self, cmdname, **para):
        if cmdname == "ls":
            if 'pool' in para :
                return True, self.prefix + self.cmdmap[cmdname] % (para['pool'],)
            else:
                return False, "need 'pool' in parameters"
        elif cmdname == "info":
            if 'pool' in para and 'image' in para:
                return True, self.prefix + self.cmdmap[cmdname] % (para['pool'], para['image'])
            else:
                return False, "need 'pool' or 'image' in parameters"
        elif cmdname == "snapls":
            if 'pool' in para and 'image' in para:
                return True, self.prefix + self.cmdmap[cmdname] % (para['pool'], para['image'])
            else:
                return False, "need 'pool' or 'image' in parameters"
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

