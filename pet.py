#!/usr/bin/env python3
from subprocess import *
import os
import signal
import click


cli = click.Group()


@cli.command()
@click.argument('name')
def start(name):
    """starts new project"""
    if os.path.exists("./projects/%s" % name):
        if not os.path.isfile("./projects/%s/_lock" % name):
            open("./projects/%s/_lock" % name, 'a')
            Popen(["./start.sh", name, "./projects/%s" % name]).communicate(input)
        else:
            click.echo("project already activated")
    else:
        click.echo("project not found")


@cli.command()
def stop():
    """stops project"""
    os.kill(os.getppid(), signal.SIGKILL)


# add working with templates
@cli.command()
@click.argument('name')
@click.option('--temp', '-m', multiple=True, default=None, help='Creates project using templates')
def create(name, temp):
    """creates new project"""
    if not os.path.exists("./projects/%s" % name):
        os.makedirs("./projects/%s" % name)
    Popen(["./create.sh", "./projects/%s" % name]).communicate(input)


@cli.command()
def list():
    """lists all projects"""
    projects = os.listdir('./projects/')
    click.echo("\n".join(projects))


if __name__ == '__main__':
    cli()
