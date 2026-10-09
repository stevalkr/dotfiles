function mkd --description="Make directory and change into it" --wraps="mkdir"
    mkdir $argv
    cd $argv[1]
end
