function fish_greeting --description="Custom greeting for Fish shell"
    echo Good Enough is Good Enough!

    if not type -q tmux
        return
    end

    set -l tmux_info (tmux ls 2>/dev/null | count)
    if test "$tmux_info" -gt 0
        set_color yellow
        echo -n "$tmux_info"
        set_color green
        echo " tmux session(s) running."
        set_color normal
    end
end
