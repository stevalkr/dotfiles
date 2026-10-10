set -gx EDITOR nvim
set -gx VISUAL nvim
set -gx FZF_DEFAULT_OPTS \
    '--height 40%' \
    --border \
    --cycle \
    '--layout=reverse' \
    '--tmux=center' \
    '--preview-window=wrap' \
    "--marker='*'" \
    '--bind=alt-j:down' \
    '--bind=alt-k:up'

if test (uname) = Darwin
    if not type -q brew
        set -l brew_shellenv (/opt/homebrew/bin/brew shellenv fish); or return
        eval $brew_shellenv
    end

    if test -d /opt/homebrew/opt/llvm/bin
        fish_add_path --global --move /opt/homebrew/opt/llvm/bin
    end
end

fish_add_path --global --move "$HOME/.local/bin"

if status is-interactive
    fish_vi_key_bindings

    zoxide init fish --cmd cd | source

    if not functions -q __direnv_export_eval
        direnv hook fish | source
    end

    set -gx fzf_directory_opts \
        '--bind=ctrl-d:reload(fd --type d --type l --color=always --strip-cwd-prefix)' \
        '--bind=ctrl-f:reload(fd --color=always)'

    if set -q TMUX
        function renew_env --on-event fish_focus_in
            set -l vars_to_sync MULTIPLEXER MULTIPLEXER_LIST \
                I3SOCK \
                KITTY_WINDOW_ID KITTY_LISTEN_ON KITTY_PID \
                WEZTERM_PANE WEZTERM_UNIX_SOCKET WEZTERM_EXECUTABLE

            for var_name in $vars_to_sync
                set -l tmux_output (command tmux showenv $var_name 2>/dev/null)
                if test -n "$tmux_output"
                    set -l parts (string split -m 1 '=' -- $tmux_output)
                    if test (count $parts) -eq 2
                        set -gx $var_name $parts[2]
                    end
                end
            end
        end
    end
end
