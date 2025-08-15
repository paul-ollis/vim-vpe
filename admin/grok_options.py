"""Script to extract option information required by VPE."""

import argparse
import re
from pathlib import Path


def main(args):
    r_option_null = re.compile(r'''(?x)
        \s+ \{ "                               # Lead up to full option name.
        (?P<name> [a-z][a-z[0-9]*) "           # Capture the full name.
        , \s* (?P<short>NULL)                  # Capture the short name.
        , \s*                                  # Lead up to the flags.
        (?P<flags> P_ [A-Z_|]+ )               # Capture the options as a block.
    ''')
    r_option = re.compile(r'''(?x)
        \s+ \{ "                               # Lead up to full option name.
        (?P<name> [a-z][a-z[0-9]*) "           # Capture the full name.
        , \s* "                                # Lead up to short name.
        (?P<short> [a-z][a-z[0-9]*) "          # Capture the short name.
        , \s*                                  # Lead up to the flags.
        (?P<flags> P_ [A-Z_|]+ )               # Capture the options as a block.
    ''')
    option_info = []
    with args.def_path.open(mode='rt', encoding='utf-8') as f:
        for line in f:
            m = r_option_null.match(line) or r_option.match(line)
            if m:
                if not line.rstrip().endswith(','):
                    line = line.rstrip() + next(f).strip()
                    m = r_option_null.match(line) or r_option.match(line)
                option_info.append(m.groups())

    single_comma_options = []
    comma_options = []
    flag_options = []

    for name, short, flag_block in option_info:
        flags = flag_block.split('|')
        if 'P_ONECOMMA' in flags:
            single_comma_options.append((name, short))
        elif 'P_COMMA' in flags:
            comma_options.append((name, short))
        if 'P_FLAGLIST' in flags:
            flag_options.append((name, short))

    print('_comma_options = set((')
    for name, short in sorted(comma_options):
        if short == 'NULL':
            print(f'    "{name}",')
        else:
            print(f'    "{name}", "{short}",')
    print('))')

    print('_single_comma_options = set((')
    for name, short in sorted(single_comma_options):
        if short == 'NULL':
            print(f'    "{name}",')
        else:
            print(f'    "{name}", "{short}",')
    print('))')

    print('_flag_options = set((')
    for name, short in sorted(flag_options):
        if short == 'NULL':
            print(f'    "{name}",')
        else:
            print(f'    "{name}", "{short}",')
    print('))')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        'Extract VPE option information from optiondefs.h')
    parser.add_argument(
        'def_path', type=Path, help='Path to optiondefs.h')
    args = parser.parse_args()
    main(args)
