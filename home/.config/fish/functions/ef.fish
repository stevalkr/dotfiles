function ef --description="Change directory and list files" --wraps="cd"
    cd $argv
    ls
end
