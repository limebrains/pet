#!/bin/bash
if [ $# -gt 1 ]; then
echo "# TEMPLATES" > "$1/project_start"
echo "# TEMPLATES" > "$1/project_stop"
for var in "${@:2}"
do
    echo "# from template: $var" >> "$1/project_start"
    cat "projects/$var/project_start" >> "$1/project_start"
    echo "" >> "$1/project_start"

    echo "# from template: $var" >> "$1/project_stop"
    cat "projects/$var/project_stop" >> "$1/project_stop"
    echo "" >> "$1/project_stop"
done
    echo '# check if correctly imported templates' >> "$1/project_start"
    $EDITOR "$1/project_start"
    echo '# check if correctly imported templates' >> "$1/project_stop"
    $EDITOR "$1/project_stop"
else
    echo '# add here shell code to be executed while entering project' > "$1/project_start"
    $EDITOR "$1/project_start"
    echo '# add here shell code to be executed while exiting project' > "$1/project_stop"
    $EDITOR "$1/project_stop"
fi
