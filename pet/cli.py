import os
from contextlib import contextmanager

import click

from pet import bl
from pet.pet_exceptions import Info, PetException

cli = click.Group()
active_project = os.environ.get('PET_ACTIVE_PROJECT', '')

# TODO: collapse deploy.sh and make.py into one with better name
# TODO: interactive tasks in ZSH
# TODO: tasks with templates
# TODO: tests


@contextmanager
def pet_exception_manager():
    try:
        yield
    except Info as ex:
        click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='magenta')
    except PetException as ex:
        click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')


def get_projects():
    project_list = []
    with pet_exception_manager():
        if bl.print_list():
            project_list = bl.print_list().splitlines()
        return project_list


class ProjectCli(click.MultiCommand):

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
        fn = os.path.join(bl.get_projects_root(), active_project, "tasks.py")
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        if name in ns:
            return ns[name]


@cli.command('init')
@click.option('--name', '-n', default=None, help="name for project")
@click.option('--templates', '-t', multiple=True, help="-t template,template... or -t template -t template")
def create_project(name, templates):
    """creates new project"""
    if not name:
        name = os.path.basename(os.getcwd())
    if len(templates) == 1:
        if templates[0].count(',') > 0:
            templates = templates[0].split(',')
    with pet_exception_manager():
        bl.create(name, templates)


@cli.command('list')
@click.option('--old', '-o', is_flag=True, help="print projects in archive")
@click.option('--tasks', '-t', is_flag=True, help="show tasks in active project")
@click.option('--tree', is_flag=True, help="show tree of all tasks in projects")
def print_list(old, tasks, tree):
    """lists all projects/ archived projects/ tasks/ all"""
    if [old, tree, tasks].count(True) > 1:
        click.secho("Only one flag at a time! I am not Mt Everest", fg='red')
        return 1
    if old:
        projects = bl.print_old()
        if projects:
            click.echo(projects)
    elif tasks:
        if active_project:
            tasks_list = bl.print_tasks(active_project)
            if tasks_list:
                click.echo(tasks_list)
        else:
            click.secho("No project activated", fg='red')
    elif tree:
        # TODO: Tree projects -|-tasks
        click.secho("Not implemented yet", fg='magenta')
    else:
        projects = bl.print_list()
        if projects:
            click.echo(projects)


@cli.command('archive')
@click.argument('project_name')
def archive(project_name):
    """archives project"""
    with pet_exception_manager():
        bl.archive(project_name=project_name)


@cli.command()
@click.argument('project_name')
def restore(project_name):
    """restores project from archive"""
    with pet_exception_manager():
        bl.restore(project_name)


@cli.command()
def register():
    """registers .pet as project folder"""
    with pet_exception_manager():
        bl.register()


@cli.command()
def clean():
    """unlocks all projects"""
    bl.clean()


if active_project:
    @cli.command()
    @click.argument('task_name')
    def task(task_name):
        """creates new task"""
        with pet_exception_manager():
            bl.create_task(active_project, task_name)

    @cli.command()
    def stop():
        """stops project"""
        with pet_exception_manager():
            bl.stop()

    @cli.command('remove')
    @click.argument('task_name')
    def remove_task(task_name):
        """removes task"""
        with pet_exception_manager():
            bl.remove_task(active_project, task_name)

    @cli.command('rename')
    @click.argument('old_task_name')
    @click.argument('new_task_name')
    def rename_task(old_task_name, new_task_name):
        """renames task"""
        with pet_exception_manager():
            bl.rename_task(active_project, old_task_name, new_task_name)

    @cli.command()
    @click.argument('task_name', nargs=-1)
    def edit(task_name):
        """edits task if given name else active project"""
        with pet_exception_manager():
            if len(task_name) > 0:
                bl.edit_task(active_project, task_name[0])
            else:
                bl.edit_project(active_project)
else:
    @cli.command('remove')
    @click.argument('project_name')
    def remove_project(project_name):
        """removes project"""
        with pet_exception_manager():
            bl.remove_project(project_name=project_name)

    @cli.command('rename')
    @click.argument('old_project_name')
    @click.argument('new_project_name')
    def rename_project(old_project_name, new_project_name):
        """renames project"""
        with pet_exception_manager():
            bl.rename_project(old_project_name, new_project_name)

    @cli.command()
    @click.argument('project_name')
    def edit(project_name):
        """edits project"""
        with pet_exception_manager():
            bl.edit_project(project_name)

    @cli.command()
    @click.argument('project_name')
    @click.argument('task_name')
    @click.option('-i', '--interactive', is_flag=True)
    @click.argument('args', nargs=-1)
    def run(project_name, task_name, interactive, args=()):
        """runs projects task"""
        with pet_exception_manager():
            bl.run_task(
                project_name=project_name, active_project=None, task_name=task_name, interactive=interactive, args=args)


def main():
    bl.get_projects_root()
    if os.environ.get('PET_ACTIVE_PROJECT', None):
        active_cli = ActiveCli()
    else:
        active_cli = click.Group()
    projects_cli = ProjectCli()

    @click.command(
        cls=click.CommandCollection,
        sources=[cli, active_cli, projects_cli],
        invoke_without_command=True
    )
    @click.option('--version', '-v', help="show program's version number and exit", is_flag=True)
    @click.pass_context
    def multi_cli(ctx, version):
        if version:
            from pet import version
            click.secho("pet version {0}".format(version))
        elif not ctx.invoked_subcommand:
            click.secho(ctx.invoke(lambda: multi_cli.get_help(ctx)))

    multi_cli()

if __name__ == '__main__':
    main()
