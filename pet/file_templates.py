# Projects

new_project_py_file_template = '''
import click
from pet.bl import start
from pet.exceptions import PetException


@click.group(chain=True, invoke_without_command=True)
@click.option('-l', is_flag=True, help="Lock project")
@click.pass_context
def cli(ctx, l):
    if ctx.invoked_subcommand is None:
        try:
            start(project_name='{0}', lock=bool(l))
        except PetException as ex:
            click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')
'''

new_project_bash_rc_template = '''
source {0}/shell_profiles
export PET_ACTIVE_PROJECT='{1}'
source {2}/start.sh
v0=$(grep -c '^{1}$' {0}/active_projects)
PS1=\"[{1}] $PS1\[\e]1;{1} ${{v0/#1/}}\a\]\[\e]2;{1} ${{v0/#1/}}\a\]\"
source {3}
trap 'source {2}/stop.sh' EXIT
{4}
'''


# Tasks

new_tasks_py_file_template = '''
import click
from pet.bl import print_tasks, run_task
from pet.exceptions import PetException
'''

new_task_for_tasks_py_template = '''

@click.command()
@click.argument('args', nargs=-1)
@click.option('-i', '--interactive', is_flag=True)
def {0}(interactive, args=()):
    try:
        run_task("{1}", "{2}", interactive, args)
    except PetException as ex:
        click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')
'''
