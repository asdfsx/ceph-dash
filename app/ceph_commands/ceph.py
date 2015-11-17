#!/usr/env/bin python
#! -*- coding: utf-8 -*-

from . import base

class ceph(base.CommandExecutor):
    def __init__(self):
        self.prefix = "ceph "
        self.cmdmap = {
                       "monstatus":"mon_status --format json",
                       "df":"df --format json",
                       "osddf":"osd df --format json",
                       "osdgetmaxosd":"osd getmaxosd --format json",
                       "osdtree":"osd tree --format json",
                       "osddump":"osd dump --format json",
                       "osdperf":"osd perf --format json",
                       "getpoolattr":"osd pool get %s %s --format json",
                       #"setpoolattr":"osd pool set %s %s %s --format json",
                       "getquota":"osd pool get-quota %s --format json",
                       #"setquota":"osd pool set-quota %s %s --format json", 
                       "poolstats":"osd pool stats --format json",
                       "pgdump":"pg dump --format json",
                       "pgstat":"pg stat --format json",
                       "authlist":"auth list --format json",
                       }


    def generate(self, cmdname, **para):
        if cmdname == "setpoolattr":
            if 'pool' in para and 'attr' in para and 'value' in para:
                return True, self.prefix + self.cmdmap[cmdname] % (para['pool'], para['attr'], para['value'])
            else:
                return False, "need 'pool', 'attr' and 'value' in parameters"
        elif cmdname == "getpoolattr":
            if 'pool' in para and 'attr' in para:
                return True, self.prefix + self.cmdmap[cmdname] % (para['pool'], para['attr'])
            else:
                return False, "need 'pool' and 'attr' in parameters"
        elif  cmdname == "getquota":
            if 'pool' in para :
                return True, self.prefix + self.cmdmap[cmdname] % (para['pool'])
            else:
                return False, "need 'pool' in parameters"
        elif cmdname == "setquota":
            if 'pool' in para and 'attr' in para and 'value' in para:
                return True, self.prefix + self.cmdmap[cmdname] % (para['pool'], para['attr'], para['value'])
            else:
                return False, "need 'pool', 'attr' and 'value' in parameters"
        else:
            return True, self.prefix + self.cmdmap[cmdname]

    def execute(self, cmdname, **para):
        isSuccess, result = self.generate(cmdname, **para)
        if isSuccess:
            try:
                execresult = self.executeCmd(result)
                return True, execresult
            except Exception, e:
                return False, e
        else:
            return False, result
       
    def __call__(self, cmdname, **para):
        return self.execute(cmdname, **para)

