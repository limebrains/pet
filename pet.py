from subprocess import *
import sys


pet_project_name = "project"
pet_project_folder = "./project_folder"

if len(sys.argv) > 1:
    print("You choose: ", str(sys.argv[1:]))

run(["./start.sh", pet_project_name, pet_project_folder])
print("EXITED")
