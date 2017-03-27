new_project_py_file_template = '''
import click
from pet.bl import start
from pet.pet_exceptions import PetException


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

new_tasks_sh_file_template = '''
import click
from pet.bl import print_tasks, run_task
from pet.pet_exceptions import PetException
'''

new_task_for_tasks_sh_template = '''

@click.command()
@click.argument('args', nargs=-1)
@click.option('--active', envvar='PET_ACTIVE_PROJECT')
@click.option('-i', '--interactive', is_flag=True)
def {0}(interactive, active="", args=()):
    try:
        run_task("{1}", "{2}", interactive, args)
    except PetException as ex:
        click.secho(ex.__class__.__name__ + ": " + ex.__str__(), fg='red')
'''
