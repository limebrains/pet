import click
import bl
import os

# TODO: META: put executable files into folder /pet/pet/ ?
# TODO: CLEANING: deploy only once, changes autocomplete in complete.bash on fly

cli = click.Group()
active = os.environ.get('PET_ACTIVE_PROJECT', False)

# TODO: do not allow creating projects and tasks with names of pet commands (this is handled in bl)

# TODO: setup in make.py add cli.remake?


# TODO: META: if deploy needs to be done once, maybe at same time create /pet/projects , /pet/old, /pet/shell_profiles ?

# TODO: recreate projects! check if changes in file templates are doing some harm
# TODO: in the end make better and correct for this version tests -> tox!

# TODO: from whiteboard
# TODO: interactive tasks

# TODO: tasks with templates
# TODO: task aliases with possible -i flag

# TODO: CLEANING: create click.secho error strings templates

# TODO: META: MAKE SOME FUCKING ORDER AT WHICH POINT WHAT FOLDERS AND FILES SHOULD EXIST

# TODO: unlock option for tasks in other shells than sh (other extensions in general)

# TODO: META: catch bl.exceptions and print their insides with fg='red' -> no checking in pet.py, only in bl.py


def get_projects():
    project_list = []
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
        fn = os.path.join(bl.get_projects_root(), active, "tasks.py")
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        if name in ns:
            return ns[name]


if active:
    @cli.command()
    def stop():
        """stops project"""
        bl.stop()


@cli.command('init')
@click.option('--name', '-n', default=None, help="name for project")
@click.option('--templates', '-t', multiple=True, help="-t template,template... or -t template -t template")
def create_project(name, templates):
    """creates new project"""
    if not name:
        name = os.path.basename(os.getcwd())
    if name not in get_projects():
        if len(templates) == 1:
            if templates[0].count(',') > 0:
                templates = templates[0].split(',')
        for template in templates:
            if template not in get_projects():
                click.secho("{0} - template not found".format(template), fg='red')
                break
        else:
            bl.create(name, templates)
    else:
        click.secho("{0} - name already taken".format(name), fg='red')

if active:
    @cli.command()
    @click.argument('name')
    def task(name):
        """creates new task"""
        if active in get_projects():
            bl.create_task(active, name)
        else:
            click.secho("{0} - project not found".format(active), fg='red')


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


if active:
    @cli.command('remove')
    @click.argument('task')
    def remove_task(task):
        """removes task"""
        if active in get_projects():
            bl.remove_task(active, task)
        else:
            click.secho("{0} - project not found".format(active), fg='red')

if not active:
    @cli.command('remove')
    @click.argument('name')
    def remove_project(name):
        """removes project"""
        if name in get_projects():
            if name != active:
                bl.remove_project(name)
            else:
                click.secho("{0} - project is active".format(name), fg='red')
        else:
            click.secho("{0} - project not found".format(name), fg='red')


@cli.command()
@click.argument('name')
def archive(name):
    """removes project"""
    if name in get_projects():
        if name != active:
            bl.archive(name)
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


if not active:
    @cli.command('rename')
    @click.argument('old')
    @click.argument('new')
    def rename_project(old, new):
        """renames project"""
        if old in get_projects():
            if new not in get_projects():
                bl.rename_project(old, new)
            else:
                click.secho("{0} - name already taken".format(new), fg='red')
        else:
            click.secho("{0} - project not found".format(old), fg='red')


if active:
    @cli.command('rename')
    @click.argument('old')
    @click.argument('new')
    def rename_task(old, new):
        """renames task"""
        if active in get_projects():
            bl.rename_task(active, old, new)
        else:
            click.secho("{0} - (active) project not found".format(old), fg='red')


if not active:
    @cli.command()
    @click.argument('name')
    def edit(name):
        """edits project"""
        if name in get_projects():
            bl.edit_project(name)
        else:
            click.secho("{0} - project not found".format(name), fg='red')

if active:
    @cli.command()
    @click.argument('name', nargs=-1)
    def edit(name):
        """edits task if given name else active project"""
        if len(name) > 0:
            if active in get_projects():
                bl.edit_task(active, name[0])
            else:
                click.secho("{0} - (active) project not found".format(active), fg='red')
        else:
            if active in get_projects():
                bl.edit_project(active)
            else:
                click.secho("{0} - (active) project not found".format(name), fg='red')

# TODO: META combine all active/ not-active into one and sort them
if not active:
    @cli.command()
    @click.argument('project')
    @click.argument('task')
    @click.option('-i', is_flag=True, help="interactive")
    @click.argument('args', nargs=-1)
    def run(project, task, i, args=()):
        """runs projects task"""
        if project in get_projects():
            bl.run_task(project, task, active, i, args)
        else:
            click.secho("{0} - project not found".format(project), fg='red')

if __name__ == '__main__':
    bl.get_projects_root_or_create()
    if os.environ.get('PET_ACTIVE_PROJECT', None):
        active_cli = ActiveCli()
    else:
        active_cli = click.Group()
    projects_cli = ProjectCli()
    multi_cli = click.CommandCollection(sources=[cli, active_cli, projects_cli])
    multi_cli()
