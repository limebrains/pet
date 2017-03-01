from subprocess import *
import sys


pet_project_start = "/home/dawid/PycharmProjects/pet/project_start"
pet_project_tmp_bashrc = "/home/dawid/PycharmProjects/pet/tmp_bashrc"
pet_project_name = "project"
pet_project_folder = "/home/dawid/PycharmProjects/pet"

if len(sys.argv) > 1:
    print("You choose: ", str(sys.argv[1:]))

run(["./start.sh", pet_project_start, pet_project_name, pet_project_tmp_bashrc, pet_project_folder])
print("EXITED")
