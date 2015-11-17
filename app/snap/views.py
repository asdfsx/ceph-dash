#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json

from flask import request
from flask import render_template
from flask import abort
from flask import redirect
from flask import url_for
from flask import jsonify
from flask import current_app
from flask.views import MethodView

from app.base import ApiResource
from app.ceph_commands import rbd


class SnapsResource(ApiResource):
    """
    Endpoint that shows overall cluster status
    """

    endpoint = 'snaps'
    url_prefix = '/snaps'
    url_rules = {
        'snaplist':{
            'rule': '/<string:poolname>/<string:imagename>',
            'method':['GET','POST','DELETE'],
        }
    }

    def __init__(self):
        MethodView.__init__(self)
        self.config = current_app.config['USER_CONFIG']

    def get(self, poolname, imagename):
        if poolname is None:
            return redirect("/pools/")
        elif imagename is None:
            return redirect("/images/"+poolname)
        else:
            cmd = rbd.rbd()
            isSuccess, execresult = cmd.execute('snapls', **{'pool':str(poolname),'image':str(imagename)})
            if not isSuccess:
                abort(500, execresult)
            snaps = json.loads(execresult)
            return render_template('snaps.html', poolname=poolname, imagename=imagename,
                                   snaps=snaps, config=self.config)
