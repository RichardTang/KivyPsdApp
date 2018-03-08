# https://pythonhosted.org/behave/tutorial.html
#
# Given we put the system in a known state before the user (or external system) starts interacting with the system (in the When steps). Avoid talking about user interaction in givens.
#
#When we take key actions the user (or external system) performs. This is the interaction with your system which should (or perhaps should not) cause some state to change.
#
#Then we observe outcomes.

功能: 单位周报
@WIP
场景: 创建周报数据库
假如< 数据库中不存在周报表格
当< 存在周报表格的生成文件
那么< 在数据库中创建周报表格

@WIP
场景: 插入当周的数据到数据库中
假如< 数据库中不存在当周的周报数据
当< 存在当周的周报数据文件
那么< 将当周周报的数据插入到周报表格中

@WIP
场景: 更新当周的数据到数据库中
假如< 数据库中存在当周的周报数据
当< 存在当周的周报数据文件，并且版本更新
那么< 将当周周报的数据删除，然后插入更新的数据到周报表格中

@WIP
场景: 生成当周的周报
假如< 数据库中存在当周的周报数据
当< 文件系统中不存在当周的周报，或者版本不是最新的
那么< 生成当周的周报到文件系统中

