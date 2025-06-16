# -*- coding: utf-8 -*-

db.define_table('blog_post',
                Field('title', requires=IS_NOT_EMPTY()),
                Field('body', 'text', requires=IS_NOT_EMPTY()),
                Field('time_stamp', 'datetime')
                )