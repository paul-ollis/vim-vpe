"""The vpe.syntax module.

This provides a Pythonic API for defining syntax.
"""
# pylint: disable=deprecated-method

# pylint: disable=unused-wildcard-import,wildcard-import
from cleversheep3.Test.Tester import *
from cleversheep3.Test.Tester import test, runModule

import support                             # pylint: disable=wrong-import-order

from vpe import syntax

_run_after = ['test_vim.py']



class BasicSyntaxUse(support.CommandsBase):
    """Core use of the Syntax context manager."""

    @test(testID='syntax-match')
    def syntax_match(self):
        """The syntax commands are generated when the Syntax context exits.

        The context is created with a prefix value. This is prepended to
        group and cluster names.

        :<vim>:

            keepalt syntax clear
            keepalt syntax match TestMain "Hello"
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            grp.add_match('Hello')
        self.check_commands()

    @test(testID='syntax-multi-match')
    def syntax_multi_match(self):
        """More than one syntax match can be created for a group.

        :<vim>:

            keepalt syntax clear
            keepalt syntax match TestMain "Hello"
            keepalt syntax match TestMain "Goodbye"
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            grp.add_match('Hello')
            grp.add_match('Goodbye')
        self.check_commands()

    @test(testID='syntax-ext-group')
    def syntax_ext_group(self):
        """External groups references are made using the std_group method.

        :<vim>:

            keepalt syntax clear
            keepalt syntax match TestMain "Hello" nextgroup=PythonMain
            keepalt syntax match TestMain "Goodbye" matchgroup=TestGroupB
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            grp_b = syn.group('GroupB')
            pygrp = syn.std_group('PythonMain')
            grp.add_match('Hello', nextgroup=pygrp)
            grp.add_match('Goodbye', matchgroup=grp_b)
        self.check_commands()

    @test(testID='syntax-cluster')
    def syntax_cluster(self):
        """The cluster method creates a Cluster object.

        The cluster object can be used with the contains argument in a match
        add_method call. The cluster object allows groups to be added. Groups
        can be added to a cluster using Group objects or names (excluding the
        syntax prefix).

        The contains argument may also be a tuple.

        :<vim>:

            keepalt syntax clear
            keepalt syntax match TestMain "Hello" contains=@TestGroupA
            keepalt syntax match TestMain "Hello" contains=TestMain,TestOther
            keepalt syntax cluster TestGroupA contains=TestConst,TestMain,TestVar
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            other = syn.group('Other')
            cl = syn.cluster('GroupA', 'Var', 'Const')
            grp.add_match('Hello', contains=cl)
            grp.add_match('Hello', contains=(grp, other))
            cl.add(grp)
        self.check_commands()

    @test(testID='syntax-ext-cluster')
    def syntax_ext_cluster(self):
        """External clusters are made with the std_cluster method.

        :<vim>:

            keepalt syntax clear
            keepalt syntax match TestMain "Hello" contains=@ExtGroup
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            cl = syn.std_cluster('ExtGroup')
            grp.add_match('Hello', contains=cl)
        self.check_commands()

    @test(testID='syntax-sync')
    def syntax_sync(self):
        """SyncGroup, created by the sync_group method.

        The SyncGroup object is very similar to Group.

        :<vim>:

            keepalt syntax clear
            keepalt syntax sync match TestMain grouphere NONE "Hello"
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.sync_group('Main')
            grp.add_match('Hello', grouphere=syntax.NONE)
        self.check_commands()

    @test(testID='syntax-preview')
    def syntax_preview(self):
        """The preview_last method is provided to help development debugging.

        :<vim>:

            keepalt syntax clear
            keepalt syntax match TestMain "Hello"
            keepalt syntax match TestMain "Goodbye"
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            grp.add_match('Hello')
            preview = syn.preview_last()
            grp.add_match('Goodbye')
        self.check_commands()
        failUnlessEqual('keepalt syntax match TestMain "Hello"', preview)

    @test(testID='syntax-cluster-empty')
    def syntax_cluster_empty(self):
        """An empty cluster is omitted from the syntax.

        :<vim>:

            keepalt syntax clear
            keepalt syntax match TestMain "Hello" contains=@TestGroupA
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            cl = syn.cluster('GroupA')
            grp.add_match('Hello', contains=cl)
        self.check_commands()

    @test(testID='syntax-cluster-all')
    def syntax_cluster_all(self):
        """A cluster containing ALL, only uses the ALL group.

        :<vim>:

            keepalt syntax clear
            keepalt syntax match TestMain "Hello" contains=@TestGroupA
            keepalt syntax cluster TestGroupA contains=ALL
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            cl = syn.cluster('GroupA', 'Other', syn.ALL)
            grp.add_match('Hello', contains=cl)
        self.check_commands()

    @test(testID='syntax-cluster-allbut')
    def syntax_cluster_allbut(self):
        """The ALLBUT can be added to a cluster after other groups.

        :<vim>:

            keepalt syntax clear
            keepalt syntax match TestMain "Hello" contains=@TestGroupA
            keepalt syntax cluster TestGroupA contains=ALLBUT,TestOther
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            cl = syn.cluster('GroupA', 'Other')
            cl.add(syn.ALLBUT)
            grp.add_match('Hello', contains=cl)
        self.check_commands()

    @test(testID='syntax-cluster-group')
    def syntax_cluster_group(self):
        """The cluster can be used to create a group.

        The new group becomes a member of the cluster.

        :<vim>:

            keepalt syntax clear
            keepalt syntax match TestMain "Hello" contains=@TestGroupA
            keepalt syntax match TestThird "Goodbyte"
            keepalt syntax cluster TestGroupA contains=TestOther,TestThird
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            cl = syn.cluster('GroupA', 'Other')
            third = cl.group('Third')
            grp.add_match('Hello', contains=cl)
            third.add_match('Goodbyte')
        self.check_commands()

    @test(testID='syntax-simple-include')
    def syntax_simple_include(self):
        """An external syntax file can be included.

        :<vim>:

            keepalt syntax clear
            keepalt runtime syntax/python.vim
            keepalt syntax match TestMain "Hello"
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            syn.include('python')
            grp.add_match('Hello')
        self.check_commands()

    @test(testID='syntax-cluster-include')
    def syntax_cluster_include(self):
        """A cluster can include an external syntax.

        :<vim>:

            keepalt syntax clear
            keepalt syntax include @TestGroupA syntax/python
            keepalt syntax match TestMain "Hello" contains=@TestGroupA
            keepalt syntax cluster TestGroupA contains=TestOther
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            cl = syn.cluster('GroupA', 'Other')
            cl.include('syntax/python')
            grp.add_match('Hello', contains=cl)
        self.check_commands()


class Groups(support.CommandsBase):
    """The Group class.

    This provides a number of method to set up matches, keywords, regions and
    highlighting.
    """

    @test(testID='syntax-grp-keywords')
    def syntax_grp_keyword(self):
        """The add_keyword method allows multiple keywords to be defined.

        :<vim>:

            keepalt syntax clear
            keepalt syntax keyword TestMain class function
            keepalt syntax keyword TestMain def contained
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            grp.add_keyword('class', 'function')
            grp.add_keyword('def', contained=True)
        self.check_commands()

    @test(testID='syntax-grp-match-offsets')
    def syntax_grp_match_offsets(self):
        """The add_match method supports offsets.

        :<vim>:

            keepalt syntax clear
            keepalt syntax match TestMain "def function()"ms=s+3,me=e-2
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            grp.add_match('def function()', ms='s+3', me='e-2')
        self.check_commands()

    @test(testID='syntax-grp-match-delims')
    def syntax_grp_match_delims(self):
        r"""The add_match method intelligently chooses delimiters.

        :<vim>:

            keepalt syntax clear
            keepalt syntax match TestMain '"def function()"'
            keepalt syntax match TestMain /['"]/
            keepalt syntax match TestMain "'\"/\+?!=^_:@$%&*;~#,."
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            grp.add_match('"def function()"')
            grp.add_match("""['"]""")
            grp.add_match(r"""'"/\+?!=^_:@$%&*;~#,.""")
        self.check_commands()

    @test(testID='syntax-grp-links')
    def syntax_grp_links(self):
        """Groups can be linked, which sets up highlight link commands.

        Group arguments may be Group instances or names. The group method also
        supports a link_to argument.

        :<vim>:

            keepalt syntax clear
            keepalt highlight! default link TestMain Constant
            keepalt highlight! default link TestOther Constant
            keepalt highlight! default link TestThird Constant
        """
        with syntax.Syntax('Test') as syn:
            main = syn.group('Main')
            syn.group('Other')
            syn.group('Third', link_to='Constant')
            ext_grp = syn.std_group('Constant')
            ext_grp.add_links(main, "Other")
        self.check_commands()

    @test(testID='syntax-grp-region')
    def syntax_grp_region(self):
        """The add_region method allows simple regions to be defined.

        :<vim>:

            keepalt syntax clear
            keepalt syntax region TestMain start="//" end="$"
            keepalt syntax region TestMain start="/*" skip="/*" end="*/" contained
        """
        with syntax.Syntax('Test') as syn:
            main = syn.group('Main')
            main.add_region(start='//', end='$')
            main.add_region(start='/*', end='*/', skip='/*', contained=True)
        self.check_commands()

    @test(testID='syntax-grp-contained')
    def syntax_grp_contained(self):
        """A group may be contained by default.

        :<vim>:

            keepalt syntax clear
            keepalt syntax keyword TestMain class function contained
            keepalt syntax keyword TestMain pass contained
            keepalt syntax keyword TestMain def
            keepalt syntax match TestMain "not in" contained
            keepalt syntax region TestMain start="//" end="$" contained
            keepalt syntax region TestMain start="/*" end="*/" contained
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main', contained=True)
            grp.add_keyword('class', 'function')
            grp.add_keyword('pass')
            grp.add_keyword('def', contained=False)
            grp.add_match('not in')
            grp.add_region(start='//', end='$')
            with grp.region() as region:
                region.start('/*')
                region.end('*/')
        self.check_commands()

    @test(testID='syntax-grp-match-lrange')
    def syntax_grp_match_lrange(self):
        r"""The add_match method supports line range constraints.

        This can be helpful when syntax highlighting buffers containing
        generated output.

        :<vim>:

            keepalt syntax clear
            keepalt syntax match TestMain "\%<5lpreamble"
            keepalt syntax match TestMain "\%>4l\%<11lwarning"
            keepalt syntax match TestMain "\%11lresult"
            keepalt syntax match TestMain "\%>11lextra info"
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            grp.add_match('preamble', lrange=(None, 4))
            grp.add_match('warning', lrange=(4, 10))
            grp.add_match('result', lidx=10)
            grp.add_match('extra info', lrange=(11, None))
        self.check_commands()

    @test(testID='syntax-grp-highlight')
    def syntax_grp_highlight(self):
        """Groups can have highlght definitions.

        This is a convenience method that just invokes vpe.highlight.

        :<vim>:

            keepalt syntax clear
            keepalt highlight TestMain default guifg='Red'
        """
        with syntax.Syntax('Test') as syn:
            main = syn.group('Main')
            main.highlight(default=True, guifg='Red')
        self.check_commands()


class Regions(support.CommandsBase):
    """The Region class is a context manager for defining region definitions.

    This provides a clean way to define complex regions.
    """

    @test(testID='syntax-region')
    def syntax_region(self):
        """The region method provides a region context manager.

        :<vim>:

            keepalt syntax clear
            keepalt syntax region TestMain start="fun" start="function" end="endfunction"me=s
            keepalt syntax region TestMain start="/*" skip="/*" end="*/"
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            with grp.region() as region:
                region.start('fun')
                region.start('function')
                region.end('endfunction', me='s')
            with grp.region() as region:
                region.start('/*')
                region.skip('/*')
                region.end('*/')
        self.check_commands()

    @test(testID='syntax-region-lrange')
    def syntax_region_lrange(self):
        r"""Line ranges can be specified.

        :<vim>:

            keepalt syntax clear
            keepalt syntax region TestMain start="\%<5lA" end="\%>4l\%<11lB"
            keepalt syntax region TestMain start="\%11lA" end="\%>11lB"
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            with grp.region() as region:
                region.start('A', lrange=(None, 4))
                region.end('B', lrange=(4, 10))
            with grp.region() as region:
                region.start('A', lidx=10)
                region.end('B', lrange=(11, None))
        self.check_commands()

    @test(testID='syntax-region-matchgroup')
    def syntax_region_matchgroup(self):
        """The matchgroup option is place in the correct position.

        :<vim>:

            keepalt syntax clear
            keepalt syntax region TestMain matchgroup=TestGroupA start="fun" end="endf"
            keepalt syntax region TestMain start="fun" matchgroup=TestGroupA end="endf"
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            grp_a = syn.group('GroupA')
            with grp.region() as region:
                region.start('fun', matchgroup=grp_a)
                region.end('endf')
            with grp.region() as region:
                region.start('fun')
                region.end('endf', matchgroup=grp_a)
        self.check_commands()

    @test(testID='syntax-region-matchgroup-add')
    def syntax_region_matchgroup_add(self):
        """A matchgroup can be added to a region.

        :<vim>:

            keepalt syntax clear
            keepalt syntax region TestMain matchgroup=TestGroupB start="fun" end="endf"
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            grp_b = syn.group('GroupB')
            with grp.region() as region:
                region.matchgroup(grp_b)
                region.start('fun')
                region.end('endf')
        self.check_commands()

    @test(testID='syntax-region-spell')
    def syntax_region_spell(self):
        """A region can contain the Spell group.

        :<vim>:

            keepalt syntax clear
            keepalt syntax region TestMain start="fun" end="endf" contains=@Spell
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            with grp.region(spell=True) as region:
                region.start('fun')
                region.end('endf')
        self.check_commands()

    @test(testID='syntax-region-nospell')
    def syntax_region_nopspell(self):
        """A region can contain the NoSpell group.

        :<vim>:

            keepalt syntax clear
            keepalt syntax region TestMain start="fun" end="endf" contains=@NoSpell
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            with grp.region(spell=False) as region:
                region.start('fun')
                region.end('endf')
        self.check_commands()

    @test(testID='syntax-region-spell-and_contains-1')
    def syntax_region_spell_contains_1(self):
        """Options spell=True, contains=grp is correctly handled.

        :<vim>:

            keepalt syntax clear
            keepalt syntax region TestMain start="fun" end="endf" contains=@Spell,TestStuff
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            grp_b = syn.group('Stuff')
            with grp.region(spell=True, contains=grp_b) as region:
                region.start('fun')
                region.end('endf')
        self.check_commands()

    @test(testID='syntax-region-spell-and_contains-2')
    def syntax_region_spell_contains_2(self):
        """Options spell=True, contains=None is correctly handled.

        :<vim>:

            keepalt syntax clear
            keepalt syntax region TestMain start="fun" end="endf" contains=@Spell
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            with grp.region(spell=True, contains=None) as region:
                region.start('fun')
                region.end('endf')
        self.check_commands()

    @test(testID='syntax-region-spell-and_contains-3')
    def syntax_region_spell_contains_3(self):
        """Options spell=None, contains=None is correctly handled.

        :<vim>:

            keepalt syntax clear
            keepalt syntax region TestMain start="fun" end="endf"
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            with grp.region(spell=None, contains=None) as region:
                region.start('fun')
                region.end('endf')
        self.check_commands()

    @test(testID='syntax-region-containedin')
    def syntax_region_spell_containedin(self):
        """Options containedin is correctly handled.

        :<vim>:

            keepalt syntax clear
            keepalt syntax region TestMain start="fun" end="endf" containedin=TestStuff
        """
        with syntax.Syntax('Test') as syn:
            grp = syn.group('Main')
            grp_b = syn.group('Stuff')
            with grp.region(spell=None, containedin=grp_b) as region:
                region.start('fun')
                region.end('endf')
        self.check_commands()
