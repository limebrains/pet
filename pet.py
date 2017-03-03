#!/usr/bin/env python3
from subprocess import *
import os
import yaml
import click


cli = click.Group()


@cli.command()
@click.argument('name')
def start(name):
    """starts new project"""
    with open("config.yaml", "r") as f:
        config = yaml.load(f)

    if name in config["project_names"] and name not in config["active"]:
        start_project(name, config)
    else:
        # correlates with nothing - to do here or... probably click will handle command not found
        pass


def start_project(name, config):
    ppid = os.getppid()
    config["active"][name] = ppid
    with open("config.yaml", "w") as f:
        yaml.dump(config, f)
    Popen(["./start.sh", name, "./projects/{}".format(name)]).communicate(input)
    config["active"].pop(name)
    with open("config.yaml", "w") as f:
        yaml.dump(config, f)


@cli.command()
def stop():
    pass


@cli.command()
@click.argument('name')
@click.option('--temp', '-m', multiple=True, default=None, help='Creates project using templates')
def create(name, temp):
    """creates new project"""
    print(name, temp)


@cli.command()
def list():
    """lists all projects"""
    with open("config.yaml", "r") as f:
        config = yaml.load(f)
    for name in config["project_names"]:
        click.echo(name)


if __name__ == '__main__':
    cli()
