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
        click.secho("{0} - project not found".format(name), fg='red')


@cli.command()
@click.option('--active', envvar='PET_ACTIVE_PROJECT')
def stop(active):
    """stops project"""
    if active:
        bl.stop()
    else:
        click.secho("project not activated", fg='red')


@cli.group()
def create():
    """creates new project or task"""


@create.command()
@click.argument('name')
@click.argument('templates', nargs=-1)
def project(name, templates):
    """creates new project"""
    if name not in get_projects():
        for template in templates:
            if template not in get_projects():
                click.secho("{0} - template not found".format(template), fg='red')
                break
        else:
            bl.create(name, templates)
    else:
        click.secho("{0} - name already taken".format(name), fg='red')


@create.command()
@click.argument('project')
@click.argument('name')
def task(project, name):
    """creates new task"""
    if project in get_projects():
        bl.create_task(project, name)
    else:
        click.secho("{0} - project not found".format(project), fg='red')


@cli.command('list')
@click.argument('old', nargs=-1)
def print_list(old):
    """lists all projects"""
    if old and old[0] == "old":
        projects = bl.print_old()
        if projects:
            click.echo(projects)
    else:
        projects = bl.print_list()
        if projects:
            click.echo(projects)


@cli.group()
def remove():
    """removes project or task"""
    pass


@remove.command()
@click.argument('project')
@click.argument('task')
def task(project, task):
    """removes task"""
    if project in get_projects():
        bl.remove_task(project, task)
    else:
        click.secho("{0} - project not found".format(project), fg='red')


@remove.command()
@click.argument('name')
@click.argument('archive_or_remove', type=click.Choice(["A", "a", "R", "r"]))
@click.option('--active', envvar='PET_ACTIVE_PROJECT')
def project(name, archive_or_remove, active=""):
    """removes project"""
    if name in get_projects():
        if name != active:
            bl.remove(name, archive_or_remove)
        else:
            click.secho("{0} - project is active".format(name), fg='red')
    else:
        click.secho("{0} - project not found".format(name), fg='red')


@cli.group()
@click.argument('name')
def restore(name):
    """restores project from archive"""
    bl.restore(name)


@cli.command()
def register():
    """registers .pet as project folder"""
    bl.register()


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
            click.secho("{0} - name already taken".format(new), fg='red')
    else:
        click.secho("{0} - project not found".format(old), fg='red')


@cli.group()
@click.pass_context
def edit(ctx):
    """helps you edit stuff"""
    pass


@edit.command()
@click.argument('name')
def project(name):
    if name in get_projects():
        bl.edit_project(name)
    else:
        click.secho("{0} - project not found".format(name), fg='red')


@edit.command()
@click.argument('project')
@click.argument('name')
def task(project, name):
    if project in get_projects():
        bl.edit_task(project, name)
    else:
        click.secho("{0} - project not found".format(project), fg='red')


@cli.command()
@click.argument('project')
@click.argument('task')
@click.argument('args', nargs=-1)
@click.option('--active', envvar='PET_ACTIVE_PROJECT')
def task(project, task, active="", args=()):
    """runs task in project"""
    bl.run_task(project, task, active, args)


@click.command()
def hello(active="", args=()):
    """description"""
    bl.run_task("new", "hello", active, args)


if __name__ == '__main__':
    bl.get_projects_root_or_create()
    if os.environ.get('PET_ACTIVE_PROJECT', None):
        active_cli = ActiveCli()
    else:
        active_cli = click.Group()
    projects_cli = ProjectCLI()
    multi_cli = click.CommandCollection(sources=[cli, active_cli, projects_cli])
    multi_cli()
