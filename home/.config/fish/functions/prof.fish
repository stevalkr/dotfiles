function prof
    if test (uname) != Darwin
        echo 'prof is supported only on macOS (it requires xcrun xctrace and open).' 1>&2
        return 1
    end

    if not type -q xcrun; or not type -q open
        echo 'prof requires Xcode command-line tools and the macOS open command.' 1>&2
        return 127
    end

    if test (count $argv) -lt 2
        echo "Usage: prof [cpu|leaks] <program> [arguments...]" 1>&2
        return 1
    end

    set mode $argv[1]
    if not string match -q -r '^(cpu|leaks)$' -- $mode
        echo "Error: Invalid mode '$mode'. Use 'cpu' or 'leaks'." 1>&2
        return 1
    end
    set -e argv[1]

    set program (realpath -q $argv[1])
    if not test -f $program
        set program (which $argv[1])
    end
    if not test -f $program
        echo "Error: $program not found" 1>&2
        return 1
    end
    set -e argv[1]

    switch $mode
        case cpu
            set output "/tmp/cpu_profile_$(whoami)_$(basename $program).trace"
            echo "Profiling $program into $output" 1>&2

            rm -rf $output
            xcrun xctrace record \
                --template 'CPU Profiler' \
                --no-prompt \
                --output $output \
                --target-stdout - \
                --launch -- $program $argv
            open $output

        case leaks
            set output "/tmp/leaks_$(whoami)_$(basename $program).trace"
            echo "Profiling $program into $output" 1>&2

            rm -rf $output
            xcrun xctrace record \
                --template Leaks \
                --no-prompt \
                --output $output \
                --target-stdout - \
                --launch -- $program $argv
            open $output

        case '*'
            echo "Unknown profiling mode: '$mode'" 1>&2
    end
end
