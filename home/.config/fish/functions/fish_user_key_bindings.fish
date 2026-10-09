function fish_user_key_bindings
  fish_default_key_bindings --mode insert
  fish_vi_key_bindings --no-erase
  bind --mode insert ctrl-n down-or-search

  for mode in default insert
    bind --mode $mode alt-delete kill-word
    bind --mode $mode alt-backspace backward-kill-word
    bind --mode $mode alt-left backward-word
    bind --mode $mode alt-right forward-word
  end
end
