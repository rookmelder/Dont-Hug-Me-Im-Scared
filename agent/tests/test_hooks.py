"""Tests for the Claude Code hooks (.claude/hooks/): feed each one JSON on stdin in a throw-away project folder
and check the exit code. 0 = pass, 2 = blocked."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / '.claude' / 'hooks'
def scope(level=4):
    lvl = f"- **Level:** {level}\n" if level is not None else ""
    return ("# SCOPE\n**Status:** authorised\n- I confirm I own these targets: **(yes / no)** — `yes`\n" + lvl +
            "## In scope (ONLY these)\n- `10.10.10.0/24` — lab\n- `box.lan`\n## Out of scope\n- everything else 99.99.99.99\n")


OK_SCOPE = scope(4)
TEMPLATE_SCOPE = (ROOT / 'engagements' / '_TEMPLATE' / 'SCOPE.md').read_text(encoding='utf-8')


def run_hook(name, proj, payload):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(proj))
    r = subprocess.run([sys.executable, '-I', str(HOOKS / name)], input=json.dumps(payload), capture_output=True,
                       text=True, env=env, cwd=str(proj), timeout=60)
    return r.returncode, r.stderr + r.stdout


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / 'agent' / 'roles').mkdir(parents=True)
        (self.tmp / 'agent' / 'roles' / 'executor.md').write_text('base: executor\n')
        (self.tmp / 'agent' / 'roles' / 'builder.md').write_text('base: builder\n')

    def engagement(self, name, scope):
        d = self.tmp / 'engagements' / name
        d.mkdir(parents=True, exist_ok=True)
        (d / 'SCOPE.md').write_text(scope, encoding='utf-8')
        (d / 'GOAL.md').write_text('goal', encoding='utf-8')

    def shell(self, cmd):
        return run_hook('guard_shell.py', self.tmp, {'tool_input': {'command': cmd}, 'cwd': str(self.tmp)})[0]


class Attribution(Base):
    def test_trailer_blocks(self):
        self.assertEqual(self.shell("git commit -m 'x\n\nCo-Authored-By: Claude <noreply@anthropic.com>'"), 2)

    def test_generated_with_blocks(self):
        self.assertEqual(self.shell("gh pr create --body 'hi\n🤖 Generated with [Claude Code](https://claude.com/claude-code)'"), 2)

    def test_describing_the_rule_passes(self):
        self.assertEqual(self.shell("git commit -m 'hook blocks Co-Authored-By: Claude trailers'"), 0)

    def test_plain_commit_passes(self):
        self.assertEqual(self.shell("git commit -m 'fix typo'"), 0)


class Files(Base):
    def test_agents_md_write_blocked(self):
        self.assertEqual(run_hook('guard_files.py', self.tmp, {'tool_input': {'file_path': str(self.tmp / 'AGENTS.md')}})[0], 2)

    def test_normal_write_passes(self):
        self.assertEqual(run_hook('guard_files.py', self.tmp, {'tool_input': {'file_path': str(self.tmp / 'a.md')}})[0], 0)

    def test_shell_redirect_to_gemini_blocked(self):
        self.assertEqual(self.shell('echo hi > GEMINI.md'), 2)


class Delegate(Base):
    def test_builder_without_files_blocked(self):
        self.assertEqual(self.shell('python agent/delegate.py --role builder --task-file t.md'), 2)

    def test_researcher_without_files_passes(self):
        (self.tmp / 'agent' / 'roles' / 'host-researcher.md').write_text('---\nbase: researcher\n---\n')
        self.assertEqual(self.shell('python agent/delegate.py --role host-researcher --task-file t.md'), 0)

    def test_builder_with_files_passes(self):
        self.assertEqual(self.shell('python agent/delegate.py --role builder --task-file t.md --files a.py'), 0)

    def test_executor_blocked_without_authorised_scope(self):
        self.engagement('lab', TEMPLATE_SCOPE)
        self.assertEqual(self.shell('python agent/delegate.py --role executor --task-file t.md'), 2)

    def test_executor_blocked_without_any_engagement(self):
        self.assertEqual(self.shell('python agent/delegate.py --role executor --task-file t.md'), 2)

    def test_executor_passes_with_authorised_scope(self):
        self.engagement('lab', OK_SCOPE)
        self.assertEqual(self.shell('python agent/delegate.py --role executor --task-file t.md'), 0)

    def test_executor_out_of_scope_target_blocked(self):
        self.engagement('lab', OK_SCOPE)
        self.assertEqual(self.shell('python agent/delegate.py --role executor --task "scan 10.10.11.5"'), 2)

    def test_executor_in_scope_target_passes(self):
        self.engagement('lab', OK_SCOPE)
        self.assertEqual(self.shell('python agent/delegate.py --role executor --task "scan 10.10.10.7 and box.lan"'), 0)

    def test_two_engagements_ambiguous(self):
        self.engagement('a', OK_SCOPE)
        self.engagement('b', OK_SCOPE)
        self.assertEqual(self.shell('python agent/delegate.py --role executor --task-file t.md'), 2)


class ScopeWrite(Base):
    def test_redirect_blocked(self):
        self.assertEqual(self.shell("echo '- 1.2.3.4' >> engagements/lab/SCOPE.md"), 2)

    def test_sed_blocked(self):
        self.assertEqual(self.shell("sed -i 's/no/yes/' engagements/lab/SCOPE.md"), 2)

    def test_cat_passes(self):
        self.assertEqual(self.shell('cat engagements/lab/SCOPE.md'), 0)


class EngagementFiles(Base):
    def test_git_add_engagement_blocked(self):
        self.assertEqual(self.shell('git add -f engagements/lab/loot/creds.txt'), 2)

    def test_git_add_project_md_blocked(self):
        self.assertEqual(self.shell('git add PROJECT.md'), 2)

    def test_other_segment_mentioning_private_path_passes(self):
        self.assertEqual(self.shell('git add -A && git status --short | grep -E "engagements|PROJECT.md"'), 0)

    def test_git_add_template_passes(self):
        self.assertEqual(self.shell('git add engagements/_TEMPLATE/SCOPE.md engagements/README.md'), 0)

    def test_commit_with_staged_engagement_file_blocked(self):
        for c in (['init', '-q'], ['config', 'user.email', 'a@b.c'], ['config', 'user.name', 'a']):
            subprocess.run(['git', *c], cwd=self.tmp, check=True)
        (self.tmp / 'engagements' / 'lab').mkdir(parents=True)
        (self.tmp / 'engagements' / 'lab' / 'x.txt').write_text('loot')
        subprocess.run(['git', 'add', '-f', 'engagements/lab/x.txt'], cwd=self.tmp, check=True)
        self.assertEqual(self.shell("git commit -m 'oops'"), 2)


class Mcp(Base):
    def call(self, **inp):
        return run_hook('guard_mcp.py', self.tmp, {'tool_name': 'mcp__hexstrike__nmap_scan', 'tool_input': inp})[0]

    def test_blocked_without_scope(self):
        self.assertEqual(self.call(target='10.10.10.5'), 2)

    def test_in_scope_passes(self):
        self.engagement('lab', OK_SCOPE)
        self.assertEqual(self.call(target='10.10.10.5', url='http://box.lan/x'), 0)

    def test_out_of_scope_blocked(self):
        self.engagement('lab', OK_SCOPE)
        self.assertEqual(self.call(target='8.8.8.8'), 2)
        self.assertEqual(self.call(target='http://evil.example.com/'), 2)

    def test_scope_in_out_of_scope_section_is_not_in_scope(self):
        self.engagement('lab', OK_SCOPE)
        self.assertEqual(self.call(target='99.99.99.99'), 2)


class SessionStart(Base):
    def test_reports_only_level_when_ready(self):
        (self.tmp / 'PROJECT.md').write_text('ok')
        (self.tmp / 'SETUP.md').write_text('ok')
        self.engagement('lab', OK_SCOPE)   # authorised, level 4
        out = run_hook('session_start.py', self.tmp, {})[1]
        self.assertIn('level 4 (god-mode)', out)
        self.assertNotIn('NOT', out)
        self.assertNotIn('missing', out)
        self.assertNotIn('10.10', out)

    def test_reports_unauthorised_without_targets(self):
        self.engagement('lab', TEMPLATE_SCOPE)
        out = run_hook('session_start.py', self.tmp, {})[1]
        self.assertIn('NOT AUTHORISED YET', out)
        self.assertNotIn('10.10', out)


class Levels(Base):
    """The level gates the workers only: the Lead (Claude) may run every command itself, at any level."""

    def test_lead_runs_every_command_at_any_level(self):
        for lvl in (1, 2, 3, None):
            self.engagement('lab', scope(lvl))
            for cmd in ('nmap -sV 10.10.10.5', 'sqlmap -u http://box.lan/', 'hping3 --flood 10.10.10.5',
                        'nmap -sV 10.10.11.9', 'true && hydra -l a -P p.txt ssh://box.lan', 'cat scans/out.txt', 'git status'):
                self.assertEqual(self.shell(cmd), 0, f'level {lvl}: {cmd}')

    def test_lead_runs_commands_without_any_engagement(self):
        self.assertEqual(self.shell('nmap -sV 10.10.10.5'), 0)

    def test_exec_allow_over_level_blocks_executor(self):
        self.engagement('lab', scope(2))
        (self.tmp / 'PROJECT.md').write_text('```settings\nexec_allow: nmap sqlmap\n```\n')
        self.assertEqual(self.shell('python agent/delegate.py --role executor --task-file t.md'), 2)

    def test_exec_allow_within_level_passes(self):
        self.engagement('lab', scope(2))
        (self.tmp / 'PROJECT.md').write_text('```settings\nexec_allow: nmap\n```\n')
        self.assertEqual(self.shell('python agent/delegate.py --role executor --task-file t.md'), 0)


class McpLevels(Base):
    def call(self, **inp):
        return run_hook('guard_mcp.py', self.tmp, {'tool_name': 'mcp__hexstrike__nmap_scan', 'tool_input': inp})[0]

    def test_nmap_blocked_at_1(self):
        self.engagement('lab', scope(1))
        self.assertEqual(self.call(target='10.10.10.5'), 2)

    def test_nmap_ok_at_2(self):
        self.engagement('lab', scope(2))
        self.assertEqual(self.call(target='10.10.10.5'), 0)


if __name__ == '__main__':
    unittest.main()
