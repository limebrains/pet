import click
import bl


cli = click.Group()


@cli.command()
@click.argument('name')
def start(name):
    """starts new project"""
    output = bl.start(name)
    if output:
        click.secho(output, fg='red')


@cli.command()
def stop():
    """stops project"""
    bl.stop()


@cli.command()
@click.argument('name')
@click.option('--templates', '-t', multiple=True, default=None, help='Creates project using templates')
def create(name, templates):
    """creates new project"""
    output = bl.create(name, templates)
    if output:
        click.secho(output, fg='red')


@cli.command()
def list():
    """lists all projects"""
    projects = bl.list()
    if projects:
        click.echo("\n".join(projects))


@cli.command()
@click.argument('name')
def remove(name):
    """removes project"""
    output = bl.remove(name)
    if output:
        click.secho(output, fg='red')


@cli.command()
def clean_up():
    """unlocks all projects"""
    bl.clean_up()


if __name__ == '__main__':
    cli()
