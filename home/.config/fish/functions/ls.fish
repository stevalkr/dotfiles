function ls --description="List directory contents with eza" --wraps="eza"
    # eza reads paths from stdin when it is not a terminal and no path is
    # given, so default to the current directory there.
    if not isatty stdin; and not string match -qv -- '-*' $argv
        set -a argv .
    end
    eza $argv
end
