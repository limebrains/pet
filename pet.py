import click
import bl
import os
from pet_exceptions import PetException

# TODO: META: put executable files into folder /pet/pet/ ?

cli = click.Group()
active = os.environ.get('PET_ACTIVE_PROJECT', False)

# TODO: correct deploy.sh
# TODO: interactive tasks in ZSH
# TODO: tasks with templates
# TODO: tests


def get_projects():
    project_list = []
    try:
        if bl.print_list():
            project_list = bl.print_list().splitlines()
        return project_list
    except PetException as ex:
        click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')


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
        fn = os.path.join(bl.get_projects_root(), active, "tasks.py")
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
    try:
        bl.create(name, templates)
    except PetException as ex:
        click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')


@cli.command('list')
@click.option('--old', '-o', is_flag=True, help="print projects in archive")
@click.option('--tasks', '-t', is_flag=True, help="show tree of all tasks in all projects")
def print_list(old, tasks):
    """lists all projects"""
    if old:
        projects = bl.print_old()
        if projects:
            click.echo(projects)
    elif tasks:
        if active:
            tasks_list = bl.print_tasks(active)
            if tasks_list:
                click.echo(tasks_list)
        else:
            # TODO: Tree projects -|-tasks
            click.secho("showing tree not implemented yet", fg='red')
    else:
        projects = bl.print_list()
        if projects:
            click.echo(projects)


@cli.command()
@click.argument('name')
def archive(name):
    """removes project"""
    try:
        bl.archive(name)
    except PetException as ex:
        click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')


@cli.command()
@click.argument('name')
def restore(name):
    """restores project from archive"""
    try:
        bl.restore(name)
    except PetException as ex:
        click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')


@cli.command()
def register():
    """registers .pet as project folder"""
    try:
        bl.register()
    except PetException as ex:
        click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')


@cli.command()
def clean():
    """unlocks all projects"""
    bl.clean()


if active:
    @cli.command()
    @click.argument('name')
    def task(name):
        """creates new task"""
        try:
            bl.create_task(active, name)
        except PetException as ex:
            click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')


    @cli.command()
    def stop():
        """stops project"""
        try:
            bl.stop()
        except PetException as ex:
            click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')


    @cli.command('remove')
    @click.argument('task')
    def remove_task(task):
        """removes task"""
        try:
            bl.remove_task(active, task)
        except PetException as ex:
            click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')


    @cli.command('rename')
    @click.argument('old')
    @click.argument('new')
    def rename_task(old, new):
        """renames task"""
        try:
            bl.rename_task(active, old, new)
        except PetException as ex:
            click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')


    @cli.command()
    @click.argument('name', nargs=-1)
    def edit(name):
        """edits task if given name else active project"""
        try:
            if len(name) > 0:
                bl.edit_task(active, name[0])
            else:
                bl.edit_project(active)
        except PetException as ex:
            click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')
else:
    @cli.command('remove')
    @click.argument('name')
    def remove_project(name):
        """removes project"""
        try:
            bl.remove_project(name)
        except PetException as ex:
            click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')


    @cli.command('rename')
    @click.argument('old')
    @click.argument('new')
    def rename_project(old, new):
        """renames project"""
        try:
            bl.rename_project(old, new)
        except PetException as ex:
            click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')


    @cli.command()
    @click.argument('name')
    def edit(name):
        """edits project"""
        try:
            bl.edit_project(name)
        except PetException as ex:
            click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')


    @cli.command()
    @click.argument('project')
    @click.argument('task')
    @click.option('-i', is_flag=True, help="interactive")
    @click.argument('args', nargs=-1)
    def run(project, task, i, args=()):
        """runs projects task"""
        try:
            bl.run_task(project, task, active, i, args)
        except PetException as ex:
            click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')


if __name__ == '__main__':
    bl.get_projects_root()
    if os.environ.get('PET_ACTIVE_PROJECT', None):
        active_cli = ActiveCli()
    else:
        active_cli = click.Group()
    projects_cli = ProjectCli()
    multi_cli = click.CommandCollection(sources=[cli, active_cli, projects_cli])
    multi_cli()
