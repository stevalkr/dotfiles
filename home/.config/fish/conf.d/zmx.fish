set -gx ZMX_NO_DETACH_KEY 1

set -gx ZMX_TRACK_ENV (string join , \
    DISPLAY SSH_AUTH_SOCK SSH_AGENT_PID SSH_CONNECTION WINDOWID XAUTHORITY \
    KITTY_LISTEN_ON KITTY_PID KITTY_WINDOW_ID \
    WEZTERM_PANE WEZTERM_UNIX_SOCKET WEZTERM_EXECUTABLE \
    MULTIPLEXER MULTIPLEXER_LIST \
    I3SOCK)

if status is-interactive; and set -q ZMX_SESSION
    function __zmx_refresh_env --on-event fish_prompt
        set -l tracked (string split , -- $ZMX_TRACK_ENV)
        set -l lines (zmx print-env . 2>/dev/null); or return
        set -l seen
        for line in $lines
            set -l kv (string split -m1 = -- $line)
            contains -- $kv[1] $tracked; or continue
            set -gx $kv[1] $kv[2]
            set -a seen $kv[1]
        end
        for var in $tracked
            contains -- $var $seen; or set -e $var
        end
    end
end
