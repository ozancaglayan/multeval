#!/usr/bin/env python
import os
import sys
import argparse
import subprocess

from collections import defaultdict, OrderedDict, Counter
from pathlib import Path

import tabulate


MULTEVAL_BIN = Path('~/git/multeval/multeval').expanduser()

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

    # Sort systems wrt METEOR
    sort_by = sort_by.upper()
    systems = sorted(
        systems, key=lambda x: float(x[header.index(sort_by)].split()[0]))
    return tabulate.tabulate([baseline] + systems, header)


def get_systems(test_set, baseline, folders=None,
                metric='meteor', beam_size=12,
                suffix=None, prefix='hyp.word', custom_fname=None):
    hypfiles = []
    systems = defaultdict(list)
    sys_dict = OrderedDict()

    glob = '{}.{}.*.{}.beam{}'.format(prefix, metric, test_set, beam_size)
    if suffix:
        glob += '.{}'.format(suffix)

    if custom_fname is not None:
        glob = custom_fname

    if folders is None:
        root = Path('.')
        hypfiles = list(root.glob('*/{}'.format(glob)))
    else:
        for folder in folders:
            hypfiles.extend(Path(folder).glob(glob))

    if len(hypfiles) == 0:
        raise Exception('No hypothesis file found with glob "{}"'.format(glob))

    # Fetch systems
    for hypfile in hypfiles:
        # Path -> list of hyp files
        systems[str(hypfile.parent)].append(str(hypfile))

    n_runs = Counter(
        [len(files) for files in systems.values()]).most_common(1)[0][0]
    print('Guessed n_runs: {}'.format(n_runs))

    for sysname in list(systems.keys()):
        if len(systems[sysname]) != n_runs:
            print('Skipping system {} with different n_runs'.format(sysname))
            del systems[sysname]
        else:
            print('Adding system {} with {} runs'.format(
                sysname, len(systems[sysname])))

    # Put baseline as first system
    if baseline not in systems:
        raise Exception('baseline {} does not exist'.format(baseline))

    # Put baseline first
    sys_dict[baseline] = systems.pop(baseline)

    # Sort the rest alphabetically
    for system in sorted(systems.keys()):
        sys_dict[system] = systems[system]

    return sys_dict

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='multeval')

    parser.add_argument('-t', '--test-set', required=True, type=str,
                        help='test set suffix i.e. test_2017_flickr/mscoco')

    parser.add_argument('-M', '--multeval-metrics', default='bleu,meteor,ter,length',
                        help='Which multeval metrics to run.')

    parser.add_argument('-l', '--language', default='de',
                        help='Language code for METEOR.')

    parser.add_argument('-b', '--baseline', required=True, type=str,
                        help='folder name for baseline system.')

    parser.add_argument('-s', '--suffix', type=str, default='',
                        help='Suffix for hypothesis file i.e. .beam12.<suff>')

    parser.add_argument('-p', '--prefix', type=str, default='hyp.word',
                        help='Prefix for hypothesis files.')

    parser.add_argument('-m', '--metric', default='meteor',
                        help='best.<metric> suffix to search for.')

    parser.add_argument('-c', '--custom-file', default=None,
                        help='Overrides -s, -p, -m and searches for the given file name instead.')

    parser.add_argument('-o', '--output-folder', default='multeval_results',
                        help='Output folder.')

    parser.add_argument('-r', '--ref', type=str, required=True,
                        help='Tokenized reference file.')

    parser.add_argument('-f', '--force', action='store_true',
                        help='Force reevaluation even folder exists.')

    parser.add_argument('-a', '--ar-shuffles', type=int, default=10000,
                        help='Approximate randomization shuffles.')

    parser.add_argument('folders', nargs='*',
                        help='List of folders to consider for evaluation.')

    # Parse arguments
    args = parser.parse_args()

    assert os.path.exists(args.ref), "Reference {} does not exist."

    # Create output folder
    out = Path(args.output_folder) / args.test_set
    if out.exists() and not args.force:
        print('Folder exists. Give -f to force evaluation.')
        sys.exit(1)

    out.mkdir(parents=True, exist_ok=True)

    multeval_metrics = args.multeval_metrics.split(',')
    if args.metric not in multeval_metrics:
        args.metric = multeval_metrics[0]

    print('Multeval metrics: {}'.format(','.join(multeval_metrics)))
    print('Hypothesis selection metric: {}'.format(args.metric))


    if len(args.folders) == 0:
        # Recursively walk through the current folder to find .log files
        args.folders = None

    sysdict = get_systems(args.test_set, args.baseline, metric=args.metric,
                          folders=args.folders, suffix=args.suffix,
                          prefix=args.prefix, custom_fname=args.custom_file)
    print('- Found {} different models (n_runs: {})'.format(
        len(sysdict), len(list(sysdict.values())[0])))

    #########################################
    # Construct multeval arguments and run it
    #########################################
    cmd = [str(MULTEVAL_BIN), "eval",
           '--refs', args.ref,
           '--rankDir', '{}/ranksys'.format(out),
           '--latex', '{}/results.tex'.format(out),
           '--names', args.baseline, *list(sysdict.keys()),
           '--hyps-baseline', *sysdict[args.baseline],
           '--ar-shuffles', str(args.ar_shuffles),
           '--metrics', *multeval_metrics]

    if 'meteor' in multeval_metrics:
        cmd.extend(["--meteor.language", args.language])

    for i, (sys_name, files) in enumerate(sysdict.items()):
        cmd += ['--hyps-sys%d' % (i + 1), *files]

    print(' '.join(cmd))
    res = subprocess.check_output(cmd, universal_newlines=True)
    fancy = fancy_multeval(res.strip(), args.metric)
    with open(out / 'results.txt', 'w') as f:
        f.write(fancy + '\n')
    print(fancy)
