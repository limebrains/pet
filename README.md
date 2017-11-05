
# Pet
 
Pet (Project Environment Tool) - is the tool to help you manage project and their tasks. 

[![travis](https://img.shields.io/travis/limebrains/pet.svg)](https://travis-ci.org/limebrains/pet)
[![coveralls](https://coveralls.io/repos/limebrains/pet/badge.svg?branch=master&service=github)](https://coveralls.io/github/limebrains/pet?branch=master)
[![Documentation Status](https://readthedocs.org/projects/pet-project-environment-tool/badge/?version=latest)](http://pet-project-environment-tool.readthedocs.io/en/latest/?badge=latest)

[Documentation](http://pet-project-environment-tool.readthedocs.io/en/latest/?badge=latest) 

## Usage

![Usage](./pet.gif)


```bash
| => pet --help
Usage: pet [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --version  show program's version number and exit
  --help         Show this message and exit.

Commands:
  archive   archives project or adds it to templates
  config    configures pet
  deploy    Deploys auto-completion
  edit      edits task if given name else active project
  init      creates new project
  list      lists all projects/ archived projects/ tasks/...
  recreate  Recreates all required folders in PET_FOLDER
  register  registers .pet as project folder
  remove    removes task or locks
  rename    renames task
  restore   restores project from archive
  run       runs projects task
  stop      stops project
  task      creates new task

```

## Installation

```
bash -c "$(curl -fsSL https://raw.githubusercontent.com/limebrains/pet/master/install.bash)"
```
