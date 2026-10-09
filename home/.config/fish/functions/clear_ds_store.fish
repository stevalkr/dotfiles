function clear_ds_store --description="Recursively delete all .DS_Store files in the current directory"
    if not type -q fd
        echo 'clear_ds_store requires fd' 1>&2
        return 127
    end
    fd -HI -tf '^\.DS_Store$' -E '.timemachine' -E 'Time Machine' -E '.Trashes' -X rm
end
