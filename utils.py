# -*- coding:utf-8 -*-
import os
import uuid
import tempfile


def generate_temp_filename():
    return os.path.join(tempfile.gettempdir(), 'sublime-sync_%s.zip' % str(uuid.uuid4()))
