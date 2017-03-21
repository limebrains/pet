new_project_py_file = '''
import click
from bl import start


@click.group(chain=True, invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        start('{0}')
'''

new_tasks_file = '''
import click
from bl import print_tasks, run_task
'''

new_task = '''

@click.command()
@click.argument('args', nargs=-1)
@click.option('--active', envvar='PET_ACTIVE_PROJECT')
@click.option('-i', is_flag=True)
def {0}(i, active="", args=()):
    run_task("{1}", "{2}", active, i, args)
'''
