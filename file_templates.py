new_project_py_file = '''
import click
import bl


@click.group(chain=True, invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        bl.start('{0}')
'''

new_tasks_file = '''
import click
import bl
'''

new_task = '''

@click.command()
@click.argument('args', nargs=-1)
@click.option('--active', envvar='PET_ACTIVE_PROJECT')
def {0}(active="", args=()):
    \"""{1}""\"
    bl.run_task("{2}", "{3}", active, args)
'''
