# -*- coding: utf-8 -*-
# encoding=utf8
import os
import sys
reload(sys)
sys.setdefaultencoding( "utf-8" )

from invoke import task
import subprocess
import pty

def reader(fd):
    try:
        while True:
            buffer = os.read(fd, 1024)
            if not buffer:
                return

            yield buffer

    # Unfortunately with a pty, an 
    # IOError will be thrown at EOF
    # On Python 2, OSError will be thrown instead.
    except (IOError, OSError) as e:
        pass

def run_behave():
    master, slave = pty.openpty()
    # direct stderr also to the pty!
    process = subprocess.Popen(
#        ['ls', '-al', '--color=auto'],
        ['behave', '--lang', 'zh-CN'],
        stdout=slave,
        stderr=subprocess.STDOUT
    )

    # close the slave descriptor! otherwise we will
    # hang forever waiting for input
    os.close(slave)

    # read chunks (yields bytes)
    for i in reader(master):
        # and write them to stdout file descriptor
        #os.write(1, b'<chunk>' + i + b'</chunk>')
        os.write(1, b'' + i + b'')

def run_command(inCommand, inArg0='', inArg1='', inArg2='', inArg3=''):
    master, slave = pty.openpty()
    # direct stderr also to the pty!
    process = subprocess.Popen(
        [inCommand, inArg0, inArg1, inArg2, inArg3],
        stdout=slave,
        stderr=subprocess.STDOUT
    )

    # close the slave descriptor! otherwise we will
    # hang forever waiting for input
    os.close(slave)

    # read chunks (yields bytes)
    for i in reader(master):
        # and write them to stdout file descriptor
        #os.write(1, b'<chunk>' + i + b'</chunk>')
        os.write(1, b'' + i + b'')

def run_command_line(inCommandLine):
    master, slave = pty.openpty()
    # direct stderr also to the pty!
    process = subprocess.Popen(
        inCommandLine.split(' '),
        stdout=slave,
        stderr=subprocess.STDOUT
    )

    # close the slave descriptor! otherwise we will
    # hang forever waiting for input
    os.close(slave)

    # read chunks (yields bytes)
    for i in reader(master):
        # and write them to stdout file descriptor
        #os.write(1, b'<chunk>' + i + b'</chunk>')
        os.write(1, b'' + i + b'')


@task
def runBehave(ctx, docs=False):
    print("###################")
    print("behave --lang zh-CN")
    print("###################")
    run_behave()

@task
def runBehaveWIP(ctx, docs=False):
    #run_command('behave', '—tags=WIP', '--lang', 'zh-CN')
    run_command('behave', '--tags', 'WIP', '--lang', 'zh-CN')
    pass

@task
def runGatsbyBuild(ctx, docs=False):
    os.chdir('ndailytask')
    #ctx.run("gatsby build")
    run_command('gatsby', 'build')
    os.chdir('..')

@task
def runGatsbyDevelop(ctx, docs=False):
    os.chdir('ndailytask')
    run_command('gatsby', 'develop')
    os.chdir('..')

@task
def runGatsbyUpload(ctx, docs=False):
    os.chdir('ndailytask')
    run_command('surge', 'public/', 'wonderful-verse.surge.sh')
    os.chdir('..')

@task
def databaseDump(ctx, docs=False):
    os.chdir('database')
    os.system('sqlite3 mydb.sqlite .dump > mydb.sql')
    os.system('cat mydb.sql')
    os.chdir('..')

@task
def databaseApply(ctx, docs=False):
    os.system('yoyo apply')

@task
def databaseRollback(ctx, docs=False):
    os.system('yoyo rollback -a')

@task
def databaseReapply(ctx, docs=False):
    os.system('yoyo reapply')

