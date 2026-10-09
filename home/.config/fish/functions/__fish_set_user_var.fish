function __fish_set_user_var --description="Set a user variable for the terminal"
    if type -q base64
        printf "\033]1337;SetUserVar=%s=%s\007" "$argv[1]" (echo -n "$argv[2]" | base64)
    end
end
