function ws --description="Change to workspace directory"
    switch (count $argv)
        case 0
            cd ~/workspace
        case 1
            switch $argv[1]
                case config
                    cd ~/.config
                case '*'
                    set -l path "$HOME/workspace/$argv[1]"
                    test -d "$path"; and cd "$path"; or begin
                        echo "Workspace does not exist: $path" 1>&2
                        return 1
                    end
            end
        case '*'
            echo 'Too many arguments. Only one argument is supported.'
            return 1
    end
    ls
end
