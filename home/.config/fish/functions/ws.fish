function ws --description="Change to workspace directory"
    switch (count $argv)
        case 0
            cd ~/Documents
        case 1
            switch $argv[1]
                case stu
                    set -l path "$HOME/Library/Mobile Documents/com~apple~CloudDocs/STU"
                    test -d "$path"; and cd "$path"; or begin
                        echo "Workspace does not exist: $path" 1>&2
                        return 1
                    end
                case play
                    cd ~/Playgrounds
                case icloud
                    set -l path "$HOME/Library/Mobile Documents"
                    test -d "$path"; and cd "$path"; or begin
                        echo "Workspace does not exist: $path" 1>&2
                        return 1
                    end
                case sing-box
                    set -l path "$HOME/Library/Mobile Documents/iCloud~io~nekohasekai~sfavt/Documents"
                    test -d "$path"; and cd "$path"; or begin
                        echo "Workspace does not exist: $path" 1>&2
                        return 1
                    end
                case config
                    cd ~/.config
                case devkit
                    cd ~/.devkit
                case '*'
                    echo Unknown argument: $argv[1]. Defaulting to ~/Documents.
                    cd ~/Documents
            end
        case '*'
            echo 'Too many arguments. Only one argument is supported.'
            return 1
    end
    ls
end
