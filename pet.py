import click
import bl


cli = click.Group()


@cli.command()
@click.argument('name')
def start(name):
    """starts new project"""
    output = bl.start(name)
    if output:
        click.secho(output, fg='red')


@cli.command()
def stop():
    """stops project"""
    bl.stop()


@cli.command()
@click.argument('name')
@click.option('--templates', '-t', multiple=True, help='Creates project using templates')
def create(name, templates):
    """creates new project"""
    output = bl.create(name, templates)
    if output:
        click.secho(output, fg='red')


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
    output = bl.remove(name)
    if output:
        click.secho(output, fg='red')


@cli.command()
def clean_up():
    """unlocks all projects"""
    bl.clean_up()


@cli.command()
@click.argument('old')
@click.argument('new')
def rename(old, new):
    """renames projects"""
    output = bl.rename(old, new)
    if output:
        click.secho(output, fg='red')


@cli.group()
@click.pass_context
def edit(ctx):
    """helps you edit stuff"""


@edit.command()
@click.argument('name')
def project(name):
    output = bl.edit_project(name)
    if output:
        click.secho(output, fg='red')


@edit.command()
@click.argument('name')
def task(name):
    bl.edit_task(name)


if __name__ == '__main__':
    cli()
