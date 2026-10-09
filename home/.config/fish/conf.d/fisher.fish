set -g fisher_path "$__fish_config_dir/fisher"

set -p fish_function_path "$fisher_path/functions"
set -p fish_complete_path "$fisher_path/completions"

if test -d "$fisher_path/conf.d"
    for fisher_conf in "$fisher_path"/conf.d/*.fish
        test -f "$fisher_conf"; and source "$fisher_conf"
    end
end
