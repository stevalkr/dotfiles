function t --wraps="tmux"
    set -l ori_multiplexer_list $MULTIPLEXER_LIST
    set -gx MULTIPLEXER_LIST "tmux,$ori_multiplexer_list"
    __fish_set_user_var IS_TMUX true

    command tmux $argv

    set -gx MULTIPLEXER_LIST $ori_multiplexer_list
    __fish_set_user_var IS_TMUX false
end
