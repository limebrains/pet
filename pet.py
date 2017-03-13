import click
import bl


cli = click.Group()


project_list = []
if bl.print_list():
    project_list = bl.print_list().splitlines()


@cli.command()
@click.argument('name')
def start(name):
    """starts new project"""
    if name in project_list:
        bl.start(name)
    else:
        click.secho("project not found", fg='red')


@cli.command()
def stop():
    """stops project"""
    bl.stop()


@cli.command()
@click.argument('name')
@click.option('--templates', '-t', multiple=True, help='Creates project using templates')
def create(name, templates):
    """creates new project"""
    if name not in project_list:
        for template in templates:
            if template not in project_list:
                click.secho("template not found", fg='red')
                break
        else:
            bl.create(name, templates)
    else:
        click.secho("name already taken", fg='red')


@cli.command('list')
@click.option('--tasks', '-t', help="List available tasks in project")
def print_list(tasks):
    """lists all projects"""
    projects = bl.print_list(tasks)
    if projects:
        click.echo(projects)


@cli.command()
@click.argument('name')
def remove(name):
    """removes project"""
    if name in project_list:
        bl.remove(name)
    else:
        click.secho("project not found", fg='red')


@cli.command()
def clean_up():
    """unlocks all projects"""
    bl.clean_up()


@cli.command()
@click.argument('old')
@click.argument('new')
def rename(old, new):
    """renames projects"""
    if old in project_list:
        if new not in project_list:
            bl.rename(old, new)
        else:
            click.secho("name already taken", fg='red')
    else:
        click.secho("project not found", fg='red')


@cli.group()
@click.pass_context
def edit(ctx):
    """helps you edit stuff"""


@edit.command()
@click.argument('name')
def project(name):
    if name in project_list:
        bl.edit_project(name)
    else:
        click.secho("project not found", fg='red')


@edit.command()
@click.argument('name')
def task(name):
    bl.edit_task(name)


if __name__ == '__main__':
    cli()
