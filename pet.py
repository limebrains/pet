from subprocess import Popen
import os
import signal
import click


cli = click.Group()


class File():

    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode

    def __enter__(self):
        self.open_file = open(self.filename, self.mode)

    def __exit__(self, *args):
        self.open_file.close()
        os.remove(self.filename)


@cli.command()
@click.argument('name')
def start(name):
    """starts new project"""
    if os.path.exists("./projects/%s" % name):
        if not os.path.isfile("./projects/%s/_lock" % name):
            lock = File(filename="./projects/%s/_lock" % name, mode='w')
            lock.__enter__()
            Popen(["./start.sh", name, "./projects/%s" % name]).communicate(input)
            lock.__exit__()
        else:
            click.secho("project already activated", fg='red')
    else:
        click.secho("project not found", fg='red')


@cli.command()
def stop():
    """stops project"""
    os.kill(os.getppid(), signal.SIGKILL)


# add working with templates
@cli.command()
@click.argument('name')
@click.option('--templates', '-t', multiple=True, default=None, help='Creates project using templates')
def create(name, templates):
    """creates new project"""
    if not os.path.exists("./projects/%s" % name):
        os.makedirs("./projects/%s" % name)
    Popen(["./create.sh", "./projects/%s" % name]).communicate(input)


@cli.command()
def list():
    """lists all projects"""
    projects = os.listdir('./projects/')
    if projects:
        click.echo("\n".join(projects))


@cli.command()
def install():
    """create"""
    Popen("./create_shell.sh")


if __name__ == '__main__':
    cli()
