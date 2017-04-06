# bashrc

new_project_rc_template = '''
source {0}{6}
export PET_ACTIVE_PROJECT='{1}'
source {2}/start.sh
PS1=\"[{1}] $PS1\"
echo -ne \"\\033]0;{1} {5}\\007"
source {3}
if [ -z "$PET_PREV_TAB_NAME" ]; then
    tab_name_at_exit=""
else
    tab_name_at_exit="$PET_PREV_TAB_NAME"
fi
trap 'echo -ne \"\\033]0;$tab_name_at_exit\\007";source {2}/stop.sh' EXIT
export PET_PREV_TAB_NAME='{1} {5}'
{4}
'''
new_start_sh_template = '''
pet_project_folder='{0}'
cd "$pet_project_folder"
# add here shell code to be executed while entering project
'''
