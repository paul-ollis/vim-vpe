#!/usr/bin/env python

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

R_DEV_BRANCH = re.compile(r'''(?x)
    (
        v  \d+
        \. \d+
        (?: \. \d+ )?
    ) $
''')
R_REL_TAG = re.compile(r'''(?x)
    (
        \d+
        \. \d+
        (?: \. \d+ )?
    )$
''')


class TempSSHKeys:
    """Context manager that provides temporary SSH keys."""
    def __enter__(self):
        shutil.copy(Path('~/.ssh/id_rsa').expanduser(), 'docker-files')
        shutil.copy(Path('~/.ssh/id_rsa.pub').expanduser(), 'docker-files')

    def __exit__(self, _exc_type, _exc_value, _traceback):
        os.unlink(Path('docker-files/id_rsa').expanduser())
        os.unlink(Path('docker-files/id_rsa.pub').expanduser())


def check_proc(proc: subprocess.CompletedProcess):
    """Die with suitable message if a subprocess failed.

    :proc: The completed subprocess object.
    """
    if proc.returncode == 0:
        return
    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    sys.exit(f'Process exited with error code {proc.returncode}\n'
             f'Executed args = {proc.args}')


def cleanup():
    """Clean up after running an extermal program."""
    subprocess.run(['rm', '-f', 'docker-files/id_rsa*'])


def run(*args, **kwargs):
    capture_output = kwargs.pop('capture_output', True)
    proc = subprocess.run(args, capture_output=capture_output, **kwargs)
    check_proc(proc)
    if capture_output:
        return proc.stdout.decode().splitlines()
    return None


def run_with_keys(*args, **kwargs):
    capture_output = kwargs.pop('capture_output', False)
    with TempSSHKeys():
        proc = subprocess.run(args, capture_output=capture_output, **kwargs)
    check_proc(proc)
    if capture_output:
        return proc.stdout.decode().splitlines()
    return None


# TODO: Copy from escapee/git_tools.py.
class ControlledPath:
    """Extended Path for Git controlled files.

    Also for uncontrolled files within a work tree. This is implemented as a
    proxy to an actual Path because using sub-classing is impractical.

    :param path:
        The name or Path for a file.
    :param code:
        The main code for this file's git status.
    :param flags:
        The additional status information flags.
    """
    code_to_flags = {
        '1': 'xy sub mh mi mw hh hi'.split(),
        '2': 'xy sub mh mi mw hh hi x_score orig_path'.split(),
        'u': 'xy sub m1 m2 m3 mw h1 h2 h3'.split(),
    }

    def __init__(self, path, code, flags):
        self.__dict__.update({
            '_path': Path(path),
            '_code': code,
            '_flags': flags,
            'staged': False,
            'unstaged': False,
            'tracked': bool(flags),
            'xy': '  ',
        })
        names = self.code_to_flags.get(self._code, ())
        self.__dict__.update(
            dict((name, value) for name, value in zip(names, flags)))

    def __getattr__(self, name):
        return getattr(self._path, name)

    def __setattr__(self, name, value):
        try:
            getattr(self._path, name)
        except AttributeError:
            self.__dict__[name] = value
        else:
            setattr(self._path, name, value)

    @property
    def pathname(self) -> str:
        """This path as a string."""
        return str(self._path)

    @property
    def x(self):
        """The X flag."""
        return self.xy[0]

    @property
    def y(self):
        """The Y flag."""
        return self.xy[1]

    @property
    def deleted_in_tree(self):
        """Test whether this file has been deleted from the working tree."""
        return self.y == 'D' and self.x in '.MARC'

    @property
    def modified_in_tree(self):
        """Test whether this file has been modified within the working tree."""
        return self.y == 'M'

    @property
    def updated_in_index(self):
        """Test whether this file has been updated in the index."""
        return self.x == 'M'

    @property
    def part_staged(self):
        """Test whether this file has partially staged changes."""
        return self.x == 'M' and self.y == 'M'

    def __str__(self):
        s = []
        flds = 'xy'.split()
        for n, v in self.__dict__.items():
            if n in flds:
                s.append(f'{n}={v}')
        return f'{self.pathname}:{".".join(s)}'


class Branch:
    """Abstraction of a branch."""
    def __init__(self, name, commit):
        self.name = name
        self.commit = commit


class Tag:
    """Abstraction of a tag."""
    def __init__(self, name, commit):
        self.name = name
        self.commit = commit
        self.obj = None


class AnnotatedTag(Tag):
    """Abstraction of an annotated tag."""
    def __init__(self, name, commit, obj):
        super().__init__(name, commit)
        self.obj = obj


class GitRepo:
    """An abstraction for a Git reposotory.

    This uses git commands under the covers, but caches information for
    efficiency. This caching assumes that only a single GitRepo instance exists
    at any time (for a give git repository) and that no external agency updates
    the repository duing the lifetime of a GitRepo instance.
    """
    def __init__(self):
        self.invalidate()

    def invalidate(self):
        """Invalidate the cache."""
        self._refs = None
        self._cur_branch = None
        self._tags = None
        self._ann_tags = None
        self._branches = None
        self._status = None

    @property
    def cur_branch(self):
        if self._cur_branch is None:
            for line in run('git', 'branch'):
                if line.startswith('* '):
                    self._cur_branch = line.split()[1]
        return self._cur_branch

    @property
    def refs(self):
        if self._refs is None:
            self._refs = {Path(v): h for h, v in (
                line.split() for line in run('git', 'show-ref', '-d'))}
        return self._refs

    @property
    def tags(self):
        self._load_tags()
        return self._tags

    @property
    def annotated_tags(self):
        self._load_tags()
        return self._ann_tags

    @property
    def branches(self):
        self._load_branches()
        return self._branches

    @property
    def stat_files(self):
        self._get_status()
        return self._status

    @property
    def changed_files(self):
        self._get_status()
        return {n: p for n, p in self._status.items() if p.tracked}

    def _load_tags(self):
        if self._tags is None:
            self._tags = {}
            self._ann_tags = {}
            for ref, h in self.refs.items():
                if ref.parent.name == 'tags':
                    name = ref.name
                    if '^' in name:
                        root, _, _ = name.partition('^')
                        t = self._tags[root]
                        self._tags[root] = Tag(root, h)
                        self._ann_tags[root] = AnnotatedTag(root, h, t.commit)
                    else:
                        self._tags[name] = Tag(name, h)

    def _load_branches(self):
        if self._branches is None:
            self._branches = {}
            for ref, h in self.refs.items():
                if ref.parent.name == 'heads':
                    self._branches[ref.name] = Branch(ref.name, h)

    # TODO: This is basically a copy from escapee/git_tools.py.
    def _get_status(self):
        """Get the status information for a work tree."""
        if self._status is None:
            self._status = status = {}
            lines = run('git', 'status', '--porcelain=v2')
            git_paths = {}
            for line in lines:
                code, line = line.split(' ', 1)
                if code in '!?':
                    flags, pathname = (), line
                elif code == '1':
                    *flags, pathname = line.split(' ', 7)
                elif code == '2':
                    *flags, paths = line.split(' ', 8)
                    pathname, orig = paths.split('\t', 1)
                    flags.append(orig)
                elif code == 'u':
                    *flags, pathname = line.split(' ', 9)
                else:
                    pass  # An optional header.
                status[pathname] = ControlledPath(pathname, code, flags)


class ReleaseView(GitRepo):
    """A release oriented view of a GitRepo."""

    @property
    def rel_tags(self):
        return sorted([
            tag for tag in self.annotated_tags.values()
            if R_REL_TAG.match(tag.name)], key=lambda t: t.name)

    @property
    def dev_branches(self):
        return sorted([
            branch for branch in self.branches.values()
            if R_DEV_BRANCH.match(branch.name)], key=lambda b: b.name)


def check_git_stable(g, args):
    """Check that the Git reposotory is in a suitable state for the release."""
    if g.changed_files and not args.allow_modified:
        sys,exit('Tree is not clean.')
    tag = g.rel_tags[-1]
    for branch in g.dev_branches:
        if branch.name[1:] == tag.name:
            break
    else:
        sys.exit(f'No branch found for tag {tag.name}')
    if tag.commit != branch.commit:
        sys.exit('Branch/tag commit mismatch for {tag.name}')


def run_docker(image_name, *volumes, net=True, display=True):
    """Run a docker image.

    :image_name: The docker image to run.
    :volumes:    Each is a tuple of host-path, mount-path.
    """
    cmd = ['docker', 'run', '-i', '-t', '--rm']
    if net:
        cmd.extend(['--net', 'host'])
    if display:
        cmd.extend(['--env', 'DISPLAY'])
    for src, dst in volumes:
        cmd.extend(['--volume', f'{src}:{dst}'])
    cmd.append(image_name)
    run(*cmd)


def main(args):
    # Define the potential docker mounts.
    xauth = Path('~/.Xauthority').expanduser(), '/home/paul/.Xauthority:rw'
    reldir = (
        Path('~/np/sw/vim-vpe/release').expanduser(), '/home/paul/release/')

    # Check that we are a well defined state.
    g = ReleaseView()
    check_git_stable(g, args)
    tag = g.rel_tags[-1]

    if not args.skip_to_release:
        # Build the documentation. This may leave the working tree modified, so
        # check for stability again.
        run('mym', 'clean', cwd='docs', capture_output=False)
        run('mym', cwd='docs', capture_output=False)
        g.invalidate()
        check_git_stable(g, args)

        # Run the tests for the development and minimal versions.
        run('python', 'run_tests', cwd='test', capture_output=False)
        run('admin/run-vim80-tests', capture_output=False)

    # Build the release zipfile and test it.
    run_with_keys(
        'dockit', '--arg', f'version={tag.name}', 'release',
        capture_output=True)
    run_docker('release', xauth, reldir)
    run_with_keys(
        'dockit', '--arg', f'version={tag.name}', 'vpe-install',
        capture_output=True)
    run_docker('vpe-install', xauth)
    print("Release complete")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser('Build and test a release.')
    parser.add_argument(
            '--allow_modified', action='store_true',
            help='Allow modifications to the working tree.')
    parser.add_argument(
            '--skip-to-release', action='store_true',
            help='Skip to the create and test release phase.')
    main(parser.parse_args())
