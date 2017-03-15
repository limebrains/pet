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


@click.command()
@click.option('--active', envvar='PET_ACTIVE_PROJECT')
def tasks(active=""):
    tasks_list = bl.print_tasks(active)
    if tasks_list:
        click.echo(tasks_list)
'''

new_task = '''

@click.command()
@click.argument('args', nargs=-1)
@click.option('--active', envvar='PET_ACTIVE_PROJECT')
def {0}(active="", args=()):
    bl.run_task("{1}", "{2}", active, args)
'''
