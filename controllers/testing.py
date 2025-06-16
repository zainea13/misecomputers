# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------



def index():
    rows = db(db.blog_post).select()
    return locals()

@auth.requires_login()
def create():
    form = SQLFORM(db.blog_post).process()
    return locals()

def show():
    post = db.blog_post(request.args(0))
    return locals()

def get_custom_menu():
    return 

response.menu = [
        (T('Home'), False, URL('default', 'index'), []),
        (T('My Sites'), False, URL('admin', 'default', 'site'), [])
    ]
