=============
Creating task
=============

To create task you need to activate project first, than use
*task* command.

Using task
==========

Running *task* command will make a script that will be available
during use of a project.

You can specify what type of a file it's going to be, but name of
a task is understood as name of a file without extension.

If extension is not provided it will create `.sh` file.

.. code::

    [project] $ pet task task_name
    or
    [project] $ pet task task_name.extension

This opens task file in $EDITOR to let you edit it.

You can change file extension freely

Running task
============

To run a task you can do it from within project:

.. code::

    [project] $ pet task_name
    or during every next invocation of a project
    [project] $ task_name

To run it from outside of a project you have to perform:

.. code::

    $ pet run project_name task_name
