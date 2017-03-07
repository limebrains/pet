#!/bin/sh
start_file="$1/project_start"
stop_file="$1/project_stop"
if [ $# -gt 1 ]; then
echo "# TEMPLATES" > "$start_file"
echo "# TEMPLATES" > "$stop_file"
shift
for var in "$@"
do
    echo "# from template: $var" >> "$start_file"
    cat "projects/$var/project_start" >> "$start_file"
    echo "" >> "$start_file"

    echo "# from template: $var" >> "$stop_file"
    cat "projects/$var/project_stop" >> "$stop_file"
    echo "" >> "$stop_file"
done
    echo '# check if correctly imported templates' >> "$start_file"
    $EDITOR "$start_file"
    echo '# check if correctly imported templates' >> "$stop_file"
    $EDITOR "$stop_file"
else
    echo '# add here shell code to be executed while entering project' > "$start_file"
    $EDITOR "$start_file"
    echo '# add here shell code to be executed while exiting project' > "$stop_file"
    $EDITOR "$stop_file"
fi
