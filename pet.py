import click
import bl


cli = click.Group()

project_list = []
if bl.print_list():
    project_list = bl.print_list().splitlines()


class MyCLI(click.MultiCommand):

    def list_commands(self, ctx):
        return []

    def get_command(self, ctx, name):
        ns = {}
        fn = "./projects/%s/%s.py" % (name, name)
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns['cli']


projects_cli = MyCLI()


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
@click.argument('templates', nargs=-1)
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
def print_list():
    """lists all projects"""
    projects = bl.print_list()
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
@click.argument('project')
@click.argument('name')
def task(project, name):
    if project in print_list:
        bl.edit_task(project, name)


@cli.command()
@click.argument('project')
@click.argument('name')
@click.argument('description')
def task(project, name, description):
    """creates new task"""
    if project in project_list:
        bl.create_task(project, name, description)

multi_cli = click.CommandCollection(sources=[cli, projects_cli])


if __name__ == '__main__':
    multi_cli()
