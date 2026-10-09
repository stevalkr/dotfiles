function s --wraps="ssh"
    __fish_set_user_var IS_SSH true

    command ssh $argv

    __fish_set_user_var IS_SSH false
end
