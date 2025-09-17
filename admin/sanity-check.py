#!/usr/bin/env python
"""A script to sanity check the VPE code base.

This covers such things as consistent version numbering.
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

fatal_error: bool = False

@dataclass
class Info:
    """Information about the VPE code base."""

    version: str

    @property
    def version_with_stop(self):
        """The version srting with a full stop appended."""
        return f'{self.version}.'

    def display(self):
        """Display the stored information."""
        s = [
            'Information summary:',
            f'  Version: {self.version}',
        ]
        print('\n'.join(s))


def error(*lines):
    """Print a number of error lines."""
    print('Error:', file=sys.stderr)
    for line in lines:
        print(f'  {line}', file=sys.stderr)


def warning(*lines):
    """Print a number of error lines."""
    print('Warning:', file=sys.stderr)
    for line in lines:
        print(f'  {line}', file=sys.stderr)


def fatal(*lines):
    """Print a number of fatal error lines."""
    global fatal_error                       # pylint: disable=global-statement

    print('Error:', file=sys.stderr)
    for line in lines:
        print(f'  {line}', file=sys.stderr)
    fatal_error = True


def extract_version() -> str:
    """Extract the version from the README file."""
    path = Path('README.rst')
    search_text = '    This is version '
    with path.open(mode='rt', encoding='utf-8') as f:
        for line in f:
            if line.startswith(search_text):
                break
        else:
            fatal(
                f'{path}: Version missing from.',
                f'  Search was for: {search_text!r}',
            )
            return ''

    version = line.split()[-1]
    if version.endswith('.'):
        version = version[:-1]
    else:
        warning(
            f'{path}: Missing full stop after version',
            f'  Search was for: {search_text!r}',
        )
    return version


def fix_file(path: Path, line_index: int, repl_line: str) -> None:
    """Fix a file by replacing a line with the given text."""
    lines = path.read_text(encoding='utf-8').splitlines()
    lines[line_index] = repl_line
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def check_version_in_file(
        expected: str,
        fix: bool,
        path: Path,
        extract: Callable[[str], str],
        build_fixed: Callable[[str], str],
        search_text: str = '',
        search_expr: str = '',
    ) -> tuple[int, int]:
    """Find the version information in a given file.

    :expected:
        The expected version string.
    :fix:
        If ``True`` then try to fix incorrect version information.
    :path:
        The ``Path`` of the file to check.
    :search_text:
        A string to look for in the file. A matching line will start with this
        string.
    :extract:
        A function, invoked on a matching line or re.match object, to extract
        the version string. :build_fixed:
        A funcion, invoked on the ``search_text`` to create the line used to
        fix the file.

    :return:
        A tuple of 2 integers. The possible values are (0, 0) no problem was
        found, (1, 0) a problem was found but not fixed and (1, 1) a problem
        was found and it was fixed.
    """
    # pylint: disable=too-many-arguments,too-many-positional-arguments

    problem = 0
    fixed = 0
    match = None

    with path.open(mode='rt', encoding='utf-8') as f:
        for line_index, line in enumerate(f):
            if search_text and line.startswith(search_text):
                break
            if search_expr:
                match = re.match(search_expr, line)
                if match:
                    break
        else:
            error(
                f'{path}: Version missing',
                f'  Search was for: {search_text!r}',
            )
            return 1, 0

    version = extract(match) if match else extract(line)
    if version != expected:
        fix_str = ''
        if fix:
            fix_file(
                path,
                line_index,
                build_fixed(search_text),
            )
            fixed = 1
            fix_str = '[Fixed]'

        error(
            f'{fix_str}{path}: Version mismatch',
            f'  Search was for: {search_text!r}',
            f'  Expected: {expected}',
            f'  Found:    {version}',
        )
        problem = 1

    return problem, fixed


def check_version(info: Info, fix: bool) -> tuple[int, int]:
    """Check that the version is consistent."""

    problem_count = 0
    fix_count = 0

    path = Path('pyproject.toml')
    search_text = 'version = '
    problem, fixed = check_version_in_file(
        info.version, fix, path,
        extract=lambda s: s.split()[-1][1:-1],
        build_fixed=lambda s: f"{s}'{info.version}'",
        search_text=search_text,
    )
    problem_count += problem
    fix_count += fixed

    path = Path('docs/guide-intro.txt')
    search_text = 'This is the documentation for version '
    problem, fixed = check_version_in_file(
        info.version_with_stop, fix, path,
        extract=lambda s: s.split()[-1],
        build_fixed=lambda s: f'{s}{info.version}.',
        search_text=search_text,
    )
    problem_count += problem
    fix_count += fixed

    path = Path('src/vpe/__init__.py')
    search_text = '__version__ = '
    problem, fixed = check_version_in_file(
        info.version, fix, path,
        extract=lambda s: s.split()[-1][1:-1],
        build_fixed=lambda s: f"{s}'{info.version}'",
        search_text=search_text,
    )
    problem_count += problem
    fix_count += fixed

    path = Path('test/test_extensions.py')
    search_expr = r"        failUnlessEqual\('([^']+)', res.version\)"
    correct_text = f"        failUnlessEqual('{info.version}', res.version)"
    problem, fixed = check_version_in_file(
        info.version, fix, path,
        extract=lambda m: m.group(1),
        build_fixed=lambda s: correct_text,
        search_expr=search_expr,
    )
    problem_count += problem
    fix_count += fixed

    mym_lines = (
        "sphinxConfig.conf['version'] = ", "sphinxConfig.conf['release'] = ")

    for search_text in mym_lines:
        for path_name in ('docs/MymMainfile', 'docs/guide/Mymfile'):
            path = Path(path_name)
            problem, fixed = check_version_in_file(
                info.version, fix, path,
                extract=lambda s: s.split()[-1][1:-1],
                build_fixed=lambda s: f"{s}'{info.version}'",
                search_text=search_text,
            )
            problem_count += problem
            fix_count += fixed

    return problem_count, fix_count


checkers = (
    check_version,
)

def main(args: argparse.Namespace):
    """Perform all checks."""

    info = Info(
        extract_version(),
    )
    info.display()
    problem_count = 0
    fix_count = 0
    if not fatal_error:
        for checker in checkers:
            problem, fixed = checker(info, args.fix)
            if problem:
                problem_count += problem
                fix_count += fixed
        if problem_count == 0:
            print("No problems found")
        else:
            error(
                f'{problem_count:2} problems found',
                f'{fix_count:2} fixed',
            )
    else:
        error(
            'Fatal error during information gathering.',
            'No checking has been performed.',
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Sanitcy check the code base.')
    parser.add_argument(
        '--fix', action='store_true', help='Automatically fix issues.')
    parsed_args = parser.parse_args()
    main(parsed_args)
