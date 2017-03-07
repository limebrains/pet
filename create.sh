#!/bin/sh

echo '# add here shell code to be executed while entering project' > "$1/project_start"
$EDITOR "$1/project_start"
echo '# add here shell code to be executed while exiting project' > "$1/project_stop"
$EDITOR "$1/project_stop"
