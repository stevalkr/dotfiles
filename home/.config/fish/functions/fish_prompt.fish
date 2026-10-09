function fish_prompt --description="Write out the prompt"
    set -l last_pipestatus $pipestatus
    set -lx __fish_last_status $status
    set -l normal (set_color normal)
    set -q fish_color_status
    or set -g fish_color_status red

    set -l color_cwd $fish_color_cwd
    set -l suffix '~>'
    if functions -q fish_is_root_user; and fish_is_root_user
        if set -q fish_color_cwd_root
            set color_cwd $fish_color_cwd_root
        end
        set suffix '#'
    end

    set -l bold_flag --bold
    set -q __fish_prompt_status_generation; or set -g __fish_prompt_status_generation $status_generation
    if test $__fish_prompt_status_generation = $status_generation
        set bold_flag
    end
    set __fish_prompt_status_generation $status_generation
    set -l status_color (set_color $fish_color_status)
    set -l statusb_color (set_color $bold_flag $fish_color_status)
    set -l prompt_status (__fish_print_pipestatus "[" "]" "|" "$status_color" "$statusb_color" $last_pipestatus)

    printf '%s\n' $prompt_status
    set_color yellow
    printf '%s' $USER
    set_color normal
    printf ' at '

    set_color magenta
    echo -n (prompt_hostname)
    set_color normal
    printf ' in '

    set_color $color_cwd
    printf '%s' (prompt_pwd -D 3)
    set_color normal

    set -g vcs (fish_vcs_prompt)
    if test "$vcs" != ""
        printf ' on'
        set_color cyan
        printf '%s' $vcs
    end
    set_color normal

    printf '\n'
    printf '%s' (fish_default_mode_prompt | string join '')
    if test -n "$VIRTUAL_ENV"
        printf "[%s] " (set_color blue)(basename $VIRTUAL_ENV)(set_color normal)
    end
    if test -n "$PIXI_PROMPT"
        if test -z "$DK_ENV"
            set DK_ENV shell
        end
        printf "<%s>" (set_color blue)"pixi $DK_ENV"(set_color normal)
    end
    if test -n "$CONDA_PROMPT_MODIFIER"
        printf "%s" (set_color blue)"$CONDA_PROMPT_MODIFIER"(set_color normal)
    end

    printf '%s ' $suffix
    set_color normal
end
