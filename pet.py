import click
import bl
import os


cli = click.Group()


def get_projects():
    project_list = []
    if bl.print_list():
        project_list = bl.print_list().splitlines()
    return project_list


class ProjectCLI(click.MultiCommand):

    def list_commands(self, ctx):
        return []

    def get_command(self, ctx, name):
        ns = {}
        if os.path.exists(os.path.join(bl.get_projects_root(), name, name + ".py")):
            fn = os.path.join(bl.get_projects_root(), name, name + ".py")
            with open(fn) as f:
                code = compile(f.read(), fn, 'exec')
                eval(code, ns, ns)
            return ns['cli']


class ActiveCli(click.MultiCommand):

    def list_commands(self, ctx):
        return []

    def get_command(self, ctx, name):
        ns = {}
        active = os.environ.get('PET_ACTIVE_PROJECT', None)
        fn = os.path.join(bl.get_projects_root(), active, "tasks.py")
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        if name in ns:
            return ns[name]


@cli.command()
@click.argument('name')
def start(name):
    """starts new project"""
    if name in get_projects():
        bl.start(name)
    else:
        click.secho("project not found", fg='red')


@cli.command()
@click.option('--active', envvar='PET_ACTIVE_PROJECT')
def stop(active):
    """stops project"""
    if active:
        bl.stop()
    else:
        click.secho("project not activated", fg='red')


@cli.command()
@click.argument('name')
@click.argument('templates', nargs=-1)
def create(name, templates):
    """creates new project"""
    if name not in get_projects():
        for template in templates:
            if template not in get_projects():
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
@click.option('--active', envvar='PET_ACTIVE_PROJECT')
def remove(name, active=""):
    """removes project"""
    if name in get_projects():
        if name != active:
            bl.remove(name)
        else:
            click.secho("project active", fg='red')
    else:
        click.secho("project not found", fg='red')


@cli.command()
def clean():
    """unlocks all projects"""
    bl.clean()


@cli.command()
@click.argument('old')
@click.argument('new')
def rename(old, new):
    """renames project"""
    if old in get_projects():
        if new not in get_projects():
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
    if name in get_projects():
        bl.edit_project(name)
    else:
        click.secho("project not found", fg='red')


@edit.command()
@click.argument('project')
@click.argument('name')
def task(project, name):
    if project in get_projects():
        bl.edit_task(project, name)
    else:
        click.secho("project not found", fg='red')


@cli.command()
@click.argument('project')
@click.argument('name')
@click.argument('description', default="description")
def task(project, name, description):
    """creates new task"""
    if project in get_projects():
        bl.create_task(project, name, description)
    else:
        click.secho("project not found", fg='red')


if __name__ == '__main__':
    if os.environ.get('PET_ACTIVE_PROJECT', None):
        active_cli = ActiveCli()
    else:
        active_cli = click.Group()
    projects_cli = ProjectCLI()
    multi_cli = click.CommandCollection(sources=[cli, active_cli, projects_cli])
    multi_cli()
