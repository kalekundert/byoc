#!/usr/bin/env python3

import pytest
import doctest
import shelldoctest
import os, re
import subprocess

from pathlib import Path
from dataclasses import dataclass, field
from textwrap import dedent, indent
from traceback import format_exception
from typing import List

DOC_DIR = Path(__file__).parents[1] / 'docs'
RST_GLOB = DOC_DIR.glob('**/*.rst')

def parse_doc_examples(path):
    # States:
    # - text
    # - text-block
    # - tab
    # - tab-block

    @dataclass
    class Block:
        name: str
        indent: int
        lines: List[str] = field(default_factory=list)
        lineno: int = 0

    @dataclass
    class Context:
        indent: int
        blocks: List[Block] = field(default_factory=list)

    curr_state = 'text'
    curr_context = Context('')
    curr_block = None

    contexts = [curr_context]

    directive_pattern = r'^(?P<indent>\s*)\.\. (?P<directive>{})::(\s(?P<arg>.*))?'
    tab_pattern = directive_pattern.format('tab')
    block_pattern = directive_pattern.format('code-block')
    indent_pattern = r'^(?P<indent>\s*).*'

    def iter_lines(path):
        with path.open() as f:
            for lineno, line in enumerate(f, 1):
                yield lineno, line

    def parse_line(line, lineno):
        nonlocal curr_block
        nonlocal curr_context

        if curr_state == 'text':

            # Found tab: create a new context
            m = re.match(tab_pattern, line)
            if m:
                curr_context = Context(m['indent'])
                curr_block = Block(m['arg'], m['indent'])
                curr_context.blocks.append(curr_block)
                contexts.append(curr_context)
                return 'tab'

            # Found code block: add to current context
            m = re.match(block_pattern, line)
            if m:
                curr_block = Block(m['arg'] or 'python', m['indent'])
                curr_context.blocks.append(curr_block)
                return 'text-block'

            # Otherwise: stay in 'text' state
            return 'text'

        if curr_state == 'tab':

            # Found code block within tab:
            m = re.match(block_pattern, line)
            if m:
                if len(m['indent']) > len(curr_context.indent):
                    return 'tab-block'

            if not line.strip():
                return curr_state

            raise AssertionError(f"{path}:{lineno}: unexpected content in '.. tab::' directive: {line!r}\nexpected: '.. code-block::'")

        if curr_state == 'text-block':
            assert curr_block

            # Found end of code block: back to text mode
            m = re.match(indent_pattern, line)
            if len(m['indent']) <= len(curr_block.indent):
                return 'text'

            if not curr_block.lines:
                curr_block.lineno = lineno

            curr_block.lines.append(line)
            return 'text-block'

        if curr_state == 'tab-block':
            assert curr_block

            # Found tab: add to current context
            m = re.match(tab_pattern, line)
            if m:
                curr_block = Block(m['arg'], m['indent'])
                curr_context.blocks.append(curr_block)
                return 'tab'

            # Found end of code block: back to text mode
            m = re.match(indent_pattern, line)
            if len(m['indent']) <= len(curr_context.indent):
                return 'text'

            if len(m['indent']) <= len(curr_block.indent):
                raise AssertionError(f"{path}:{lineno}: unexpected content in '.. tab:: directive: {line!r}")

            if not curr_block.lines:
                curr_block.lineno = lineno

            curr_block.lines.append(line)
            return 'tab-block'

    for lineno, line in iter_lines(path):
        curr_state = parse_line(line, lineno)

    return contexts


@pytest.mark.parametrize(
        'rst_path', [
            pytest.param(p, id=f'{p.relative_to(DOC_DIR).stem}')
            for p in RST_GLOB
        ],
)
def test_doc_examples(rst_path, tmp_path):
    contexts = parse_doc_examples(rst_path)
    runner = doctest.DocTestRunner()
    parsers = {
            'python': doctest.DocTestParser(),
            'bash': shelldoctest.ShellDocTestParser(),
    }
    examples = []
    rst_name = str(rst_path.relative_to(DOC_DIR))

    for i, context in enumerate(contexts, 1):
        test_dir = tmp_path / f'context_{i}'
        test_dir.mkdir()

        examples += [
                doctest.Example(f'chdir({str(test_dir)!r})', ''),
        ]

        for block in context.blocks:
            source = dedent(''.join(block.lines))

            if block.name in parsers:
                parser = parsers[block.name]
                examples_ = parser.get_examples(source, rst_name)

                for example in examples_:
                    example.lineno += block.lineno

                examples += examples_

            else:
                file_path = test_dir / block.name
                file_path.write_text(source)

    class PytestRunner(doctest.DocTestRunner):

        def report_failure(self, out, test, example, got):
            pytest.fail(f"doctest gave unexpected output\nexample:\n{indent(example.source, '  ')}\nwanted:\n{indent(example.want, '  ')}\ngot:\n{indent(got, '  ')}\nlocation:\n  {rst_name}:{example.lineno}")

        def report_unexpected_exception(self, out, test, example, exc_info):
            pytest.fail(f"doctest raised unexpected exception\nexample:\n{indent(example.source, '  ')}\nerror:\n{indent(''.join(format_exception(*exc_info)), '  ')}\nlocation:\n  {rst_name}:{example.lineno}")

    class EvalOutputChecker(doctest.OutputChecker):

        def check_output(self, want, got, optionflags):
            if super().check_output(want, got, optionflags):
                return True

            # If the strings don't match, see if they compare equal when 
            # evaluated.  This accounts for things like the non-deterministic 
            # order in which items are stored in sets.
            try:
                return eval(want) == eval(got)
            except Exception:
                return False

    globs = {
            'chdir': os.chdir,
            'shell': shelldoctest.shell,
    }
    tests = doctest.DocTest(examples, globs, rst_name, rst_name, None, None)

    runner = PytestRunner(
            checker=EvalOutputChecker(),
            optionflags=doctest.IGNORE_EXCEPTION_DETAIL,
    )
    runner.run(tests)
