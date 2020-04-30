#!/usr/bin/env python
import os
import sys
import argparse
import subprocess

from collections import defaultdict, OrderedDict, Counter
from pathlib import Path

import tabulate



def fancy_multeval(output, sort_by):
    def get_fields(line):
        fields = line.strip().split()
        # find 1st metric position
        start_idx = [field[0] == '(' for field in fields].index(True) - 1
        result = [' '.join(fields[:start_idx])]
        fields = fields[start_idx:]
        result.extend([' '.join((k, v)) for k, v in zip(fields[::2], fields[1::2])])
        return result

    systems = []

    # Parse multeval outputs to fix table
    lines = output.split('\n')
    header = [x for x in lines.pop(0).split(' ') if x and x[0] != '(']
    header = [' '.join(header[:5])] + [h.upper() for h in header[5:]]

    # Pop baseline
    baseline = get_fields(lines.pop(0))

    for line in lines:
        line = line.strip()
        if line and line[0] != '*':
            fields = get_fields(line)
            if not len(fields) >= 4:
                continue
            # Shorten name
            fields[0] = fields[0].split(':')[-1].strip()
            systems.append(fields)

    # Sort systems wrt `sort_by`
    sort_by = sort_by.upper()
    systems = sorted(
        systems, key=lambda x: float(x[header.index(sort_by)].split()[0]))
    return tabulate.tabulate([baseline] + systems, header)


def get_systems(baseline, suffix, folders=None):
    hypfiles = []
    systems = defaultdict(set)
    sys_dict = OrderedDict()

    glob = f'*.{suffix}'

    if folders is None:
        root = Path('.')
        hypfiles = list(root.glob('*/{}'.format(glob)))
    else:
        for folder in folders + [baseline]:
            hypfiles.extend(Path(folder).glob(glob))

    if len(hypfiles) == 0:
        raise Exception(f'No hypothesis file found with glob {glob!r}')

    # Fetch systems
    for hypfile in hypfiles:
        # Path -> list of hyp files
        systems[str(hypfile.parent)].add(str(hypfile))

    n_runs = Counter(
        [len(files) for files in systems.values()]).most_common(1)[0][0]

    for sysname in list(systems.keys()):
        if len(systems[sysname]) != n_runs:
            print(f'Skipping system {sysname} with different n_runs')
            del systems[sysname]
        else:
            print(f'Adding system {sysname} with {len(systems[sysname])} runs')

    # Put baseline first
    sys_dict[baseline] = sorted(list(systems.pop(baseline)))

    # Sort the rest alphabetically
    for system in sorted(systems.keys()):
        sys_dict[system] = sorted(list(systems[system]))

    return sys_dict, n_runs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='multeval')

    parser.add_argument('-t', '--test-set', required=True, type=str,
                        help='test set suffix i.e. test_2017_flickr/mscoco')

    parser.add_argument('-m', '--metrics', default='bleu,meteor,ter',
                        help='Which multeval metrics to run. (First one used as primary.)')

    parser.add_argument('-l', '--language', type=str, default='',
                        help='Language code for METEOR.')

    parser.add_argument('-b', '--baseline', required=True, type=str,
                        help='folder name for baseline system.')

    parser.add_argument('-s', '--suffix', type=str, required=True,
                        help='Suffix glob for hypothesis files')

    parser.add_argument('-o', '--output-folder', default='multeval_results',
                        help='Output folder.')

    parser.add_argument('-r', '--ref', type=str, required=True,
                        help='Tokenized reference file.')

    parser.add_argument('-f', '--force', action='store_true',
                        help='Force reevaluation even folder exists.')

    parser.add_argument('-a', '--ar-shuffles', type=int, default=10000,
                        help='Approximate randomization shuffles.')

    parser.add_argument('folders', nargs='*',
                        help='List of folders to consider for evaluation excluding baseline.')

    # Parse arguments
    args = parser.parse_args()

    metrics = [m.lower() for m in args.metrics.split(',')]
    main_metric = metrics[0]
    if 'meteor' in metrics and not args.language:
        print('--language is required for METEOR metric.')
        sys.exit(1)

    if not os.path.exists(args.ref):
        print(f'reference {args.ref!r} does not exist.')
        sys.exit(1)

    # Create output folder
    out = Path(args.output_folder) / args.test_set
    if out.exists() and not args.force:
        print('Folder exists. Give -f to force evaluation.')
        sys.exit(1)

    out.mkdir(parents=True, exist_ok=True)

    if len(args.folders) == 0:
        # Recursively walk through the current folder to find .log files
        args.folders = None

    sysdict, n_runs = get_systems(args.baseline, folders=args.folders, suffix=args.suffix)
    print(f'- Found {len(sysdict)} different models (n_runs: {n_runs})')

    #########################################
    # Construct multeval arguments and run it
    #########################################
    baseline_files = sysdict.pop(args.baseline)
    cmd = ["multeval", "eval",
           '--refs', args.ref,
           '--rankDir', f'{out}/ranksys',
           '--latex', f'{out}/results.tex',
           '--names', args.baseline, *list(sysdict.keys()),
           '--hyps-baseline', *baseline_files,
           '--ar-shuffles', str(args.ar_shuffles),
           '--metrics', *metrics]

    if 'meteor' in metrics:
        cmd.extend(["--meteor.language", args.language])

    for i, (sys_name, files) in enumerate(sysdict.items()):
        cmd += [f'--hyps-sys{i + 1}', *files]

    res = subprocess.check_output(cmd, universal_newlines=True)
    fancy = fancy_multeval(res.strip(), main_metric)
    with open(out / 'results.txt', 'w') as f:
        f.write(fancy + '\n')
    print(fancy)
