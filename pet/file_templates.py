# bashrc

new_project_rc_template = '''
dir=$(pwd)
source './local.entry.sh'
source {0}
export PET_ACTIVE_PROJECT='{1}'
source {2}
PS1="[{1}] $PS1"
echo -ne "\\033]0;{1} {3}\\007"
source {4}
if [ -z "$PET_PREV_TAB_NAME" ]; then
    tab_name_at_exit=""
else
    tab_name_at_exit="$PET_PREV_TAB_NAME"
fi
trap 'echo -ne "\\033]0;$tab_name_at_exit\\007";source "$dir/local.exit.sh";source {5}' EXIT
export PET_PREV_TAB_NAME='{1} {3}'
{6}
'''

new_start_sh_template = '''
cd "$pet_project_folder"
# add here shell code to be executed while entering project
'''

new_stop_sh_template = '''
# add here shell code to be executed while exiting project
'''


edit_file_popen_template = """
PET_EDITOR=$(grep '^EDITOR==' {0} | sed -n "/EDITOR==/s/EDITOR==//p")
if [ $(command -v "$PET_EDITOR") ]; then
    $PET_EDITOR {1}
else
    if [ $(command -v "$EDITOR") ]; then
        $EDITOR {1}
    else
        echo "haven't found either '$EDITOR', either 'EDITOR==' in pet config - trying vi"
        /usr/bin/vi {1}
    fi
fi
"""

auto_complete_zsh_deploy = """
autoload -U +X compinit && compinit
autoload -U +X bashcompinit && bashcompinit
source "{0}"
"""
