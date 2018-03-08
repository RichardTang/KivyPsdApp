# -*- coding: utf-8 -*-
# encoding=utf8
from behave import *
import os
import pprint

from sqlalchemy import create_engine
from sqlalchemy import inspect

@given(u'< 数据库中不存在周报表格')
def step_impl(context):
    db_uri = 'sqlite:///database/mydb.sqlite'
    engine = create_engine(db_uri)

    inspector = inspect(engine)

    # Get table information
    #print inspector.get_table_names()
    flagFoundWsrTable = False
    for table_name in inspector.get_table_names():
        if(table_name == 'wsr_task'):
            flagFoundWsrTable = True
        #for column in inspector.get_columns(table_name):
        #    print("Column: %s.%s" % (table_name, column['name']))
        #    pprint.pprint(column)
            
            
    # Get column information
    #print inspector.get_columns('field')
    if (flagFoundWsrTable==False):
        raise NotImplementedError(u'STEP: Given < 数据库中不存在周报表格')
        

@when(u'< 存在周报表格的生成文件')
def step_impl(context):
    raise NotImplementedError(u'STEP: When < 存在周报表格的生成文件')

@then(u'< 在数据库中创建周报表格')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then < 在数据库中创建周报表格')

@given(u'< 数据库中不存在当周的周报数据')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given < 数据库中不存在当周的周报数据')

@when(u'< 存在当周的周报数据文件')
def step_impl(context):
    raise NotImplementedError(u'STEP: When < 存在当周的周报数据文件')

@then(u'< 将当周周报的数据插入到周报表格中')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then < 将当周周报的数据插入到周报表格中')

@given(u'< 数据库中存在当周的周报数据')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given < 数据库中存在当周的周报数据')

@when(u'< 存在当周的周报数据文件，并且版本更新')
def step_impl(context):
    raise NotImplementedError(u'STEP: When < 存在当周的周报数据文件，并且版本更新')

@then(u'< 将当周周报的数据删除，然后插入更新的数据到周报表格中')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then < 将当周周报的数据删除，然后插入更新的数据到周报表格中')

@when(u'< 文件系统中不存在当周的周报，或者版本不是最新的')
def step_impl(context):
    raise NotImplementedError(u'STEP: When < 文件系统中不存在当周的周报，或者版本不是最新的')

@then(u'< 生成当周的周报到文件系统中')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then < 生成当周的周报到文件系统中')

