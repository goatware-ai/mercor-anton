
#!/usr/bin/env python3
"""Reward grader with multi-framework, per-test FAIL_TO_PASS enforcement.

reward=1 requires ALL of:
  1. the test command exited 0
  2. the output does not look like "no tests were executed at all"
  3. EVERY FAIL_TO_PASS test is individually OBSERVED, in the framework's own STRUCTURED
     per-test output, as run AND PASSED — pytest/unittest -v, `go test -v`/`-json`, cargo
     libtest/nextest, ctest, `dotnet test` detailed (`Passed <name>`), gradle testLogging,
     and JUnit/xUnit/trx XML (jest-junit, mocha-junit, phpunit --log-junit, gradle
     TEST-*.xml). A required test that is absent (never observed run) or observed only on a
     failing line scores 0.

Design (Fix G, rewardhack/grader verdicts): an agent can forge the process exit code
(os.Exit(0), `|| true`, a rigged in-repo runner, a disabled build) AND forge an aggregate
pass-count / summary line ("2 passing", "Tests run: N, Failures: 0", "Passed! - Failed: 0").
It CANNOT forge the framework emitting a per-test PASS for the exact required test it
suppressed. So reward is driven ONLY by observed per-test outcomes for each configured
FAIL_TO_PASS id. There is deliberately NO aggregate-count fallback, NO synthetic-id
fallback, and NO "name visible on a non-failure line" fallback — every such fallback
accepted a forgeable signal without proving each required test actually ran and passed.
"""
import argparse, html as _html, json, re, sys

# Terminal color/escape sequences. pytest/jest/cargo/etc emit these when color is forced (e.g.
# --color=yes or a pseudo-TTY), and they sit BETWEEN the node id and its "PASSED"/"ok" marker
# ("<node> \x1b[32mPASSED\x1b[0m"), which would break every per-test regex. Strip before parsing.
_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\r")

_ZERO_RUN = re.compile(
    r"no tests ran|no tests to run|no tests found|no test files found"
    r"|collected 0 items|ran 0 tests|0 tests, 0 assertions|Executed 0 of"
    r"|no test specification|Tests:\s+0 |Test Files\s+0 ",
    re.I,
)
_FAIL_MARK = re.compile(r"\bFAILED\b|\bFAILURE\b|\bFAIL\b|\bERRORED\b|✗|✘|not ok", re.I)
# A per-test PASS marker on the SAME line overrides a fail-WORD that is merely part of the test name
# (real test names contain "fail"/"error"/"invalid": e.g. jest/vitest `✓ should support failed bdd
# steps`, mocha `✓ should fail if invalid`, tap `ok 3 - rejects failure`). Without this, a passing
# test whose description contains "fail" is misread as a failure by the lenient heuristic.
_PASS_MARK = re.compile(r"✓|✔|√|\bPASSED\b|\bpassing\b|(?:^|\s)ok\s+\d|\bPASS\b")
_JSON_FALSY_FAIL = re.compile(r'"[^"]*fail[^"]*"\s*:\s*(false|0|\[\]|null|"")', re.I)
# PER-TEST pass marker (jest/vitest/mocha `✓ <title>`, tap `ok N - <desc>`, JUnit `PASSED`). Excludes
# the summary word "passing"/"PASS" so a bare forged summary line ("2 passing (1ms)") is NOT accepted.
_JS_PERTEST = re.compile(r"✓|✔|√|\bPASSED\b|(?:^|\s)ok\s+\d+\b")
_VERBOSE_MARK = re.compile(r"\bPASSED\b|\bFAILED\b|\bXFAIL\b|\bXPASS\b|\.\.\.\s+ok\b|\.\.\.\s+(FAIL|ERROR)\b|✓|✗")

# pytest -v "<node> PASSED" and -rA "PASSED <node>" (case-sensitive: pytest emits UPPERCASE per-test)
# FIX(jeff-audit d4): a pytest parametrized id may contain SPACES inside its bracket
# (`test_comma_split_regex[1, 2, 3-output0]`). The old `\S+` cut the id at the first space,
# producing `...[1,` which no configured id could ever match.
# FIX(jeff-audit d4): a parametrized id may contain NESTED brackets
# (`test_x[CSR[bra,filled,sorted]->Number]`). `[^\]]*` stopped at the first inner `]` and
# truncated the id, so it could never match. Greedy to the last `]` on the line instead;
# the trailing outcome word still anchors the match.
_PYTEST_ID = r"(?:\S+::[^\s\[]+(?:\[.*\])?)"
# pytest-subtests / unittest subTest: the parent prints PASSED, each failing case prints SUBFAILED
_SUBFAIL_TOK = re.compile(r"\bSUB(?:FAILED|FAIL|ERROR)\b")
# A dotted CLASS-qualified id (`Ns.Cls.Should_X`, `pkg.Cls.test`) -- every segment is an identifier
# and there is no whitespace. Free-text test TITLES also contain dots ("loads config.json first"),
# and treating those as qualified wrongly rejected legitimate JS/TS matches, so they must not match.
_DOTTED_ID = re.compile(r"^[A-Za-z_][\w-]*(?:\.[A-Za-z_][\w-]*){2,}$")
_SUBFAIL_ID = re.compile(r"(\S+::[^\s\[]+)")
_PYTEST = re.compile(
    r"^\s*(" + _PYTEST_ID + r")\s+(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b"
    r"|^\s*(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\s+(" + _PYTEST_ID + r")")
# Go `go test -v`: "--- PASS: TestName (0.00s)" / "--- FAIL:" / "--- SKIP:" (subtests too)
_GO_V = re.compile(r"^\s*--- (PASS|FAIL|SKIP): (\S+)")
# Go `go test -json`: {"Action":"pass|fail|skip",...,"Test":"..."} (either field order)
# FIX(jeff-audit d4): some emitters pretty-print `{"Action": "pass", ... "Test": "..."}`.
_GO_JSON_AT = re.compile(r'"Action"\s*:\s*"(pass|fail|skip)"[^{}]*?"Test"\s*:\s*"([^"]+)"')
_GO_JSON_TA = re.compile(r'"Test":"([^"]+)"[^{}]*?"Action":"(pass|fail|skip)"')
# cargo-nextest: "PASS [   0.0s] pkg module::test" / "FAIL [...]"
# FIX(jeff-audit d4): cargo-nextest prints an optional progress counter between the timing bracket
# and the binary name — `PASS [ 0.023s] ( 3/10) nix::test-prctl test_prctl::test_get_set_name`.
# The old pattern's bare `\S+` swallowed `(` and recorded the test id as `3/10)`, so NO configured
# FAIL_TO_PASS id could ever match on a nextest task and every one of them fail-closed to 0.
_NEXTEST = re.compile(
    r"^\s*(PASS|PASSED|FAIL|FAILED|SKIP|SKIPPED)\s+\[[^\]]*\]\s+(?:\(\s*\d+\s*/\s*\d+\s*\)\s+)?(.+?)\s*$")
# FIX(jeff-audit d4): one pattern now covers every `<verb> [timing] <id>` runner seen in the corpus:
#   cargo-nextest two-token  `PASS [ 0.0s] ( 3/10) crate::bin test::name`
#   cargo-nextest one-token  `PASS [0.001s] 0xf00d::tests::test_address`
#   rspec/mocha bracket form `PASSED [ 0.001s] WebAuthn::U2fMigrator returns the public key`
# The old regex demanded exactly two whitespace-separated tokens, so single-token lines and
# space-containing test names produced ZERO parsed nodes and the task fail-closed.
# FIX(jeff-audit d4): TAP (node:test, tape, AVA, testem/QUnit). Previously unparsed entirely.
#   `ok 1 - finds an exact match`      `not ok 3 - ...`      `ok 5 - set # time=1.1ms`
#   testem prefixes a browser+timing:  `ok 1 Firefox 140.0 - [514 ms] - Integration | it renders`
# FIX(jeff-audit d4): reporters whose green output grade.py could not read at all.
#   `suite::equal_test : OK`                     custom C/C++ harnesses
#   `[PASS] test_foo() (gas: 45769)`             foundry / forge
#   `Test Case 'Cls.testX' passed (0.0 seconds)` XCTest
#   `render async layout ... ok (195ms)`         deno test
#   `[info] - should do the thing`               sbt / scalatest
#   `5 [chromium] > spec.ts:294:7 > Copy > all`  playwright list reporter
# the NAME itself may contain colons (`suite::equal_test`); the separator is a SPACED colon
_NAME_OK = re.compile(r"^[ \t]*(\S[^\n]{2,120}?)[ \t]+:[ \t]+(OK|FAILED|FAIL)[ \t]*$", re.M)
_FOUNDRY = re.compile(r"^\s*\[(PASS|FAIL)\]\s+(\S+?)\s*(?:\(gas:[^)]*\))?\s*$", re.M)
_XCTEST = re.compile(r"^\s*Test Case '([^']+)'\s+(passed|failed)\b", re.M)
_DENO = re.compile(r"^\s*(\S[^\n]{2,120}?)\s+\.\.\.\s+(ok|FAILED)\b", re.M)
_SBT = re.compile(r"^\s*\[info\]\s+-\s+(\S[^\n]{2,160}?)\s*(?:\(\d+\s*m?s\))?\s*$", re.M)
_PLAYWRIGHT = re.compile(r"^\s*\d+\s+(?:\[[^\]]+\]\s+)?[\u203a>]\s*(\S[^\n]{2,200}?)\s*(?:\(\d+(?:\.\d+)?[ms]+\))?\s*$", re.M)
_TAP = re.compile(r"^\s*(not ok|ok)\s+\d+\s*(?:-\s*)?(.+?)\s*$", re.M)
_TAP_STRIP = re.compile(r"\s+#\s*(time=|SKIP|TODO).*$|^[\w.]+ [\d.]+ - \[\s*\d+\s*ms\s*\] - ")
_LIBTEST = re.compile(r"^test\s+(\S+)\s+\.\.\.\s+(ok|FAILED|ignored)\b")
# ctest: "1/2 Test #1: name .......... Passed" / "***Failed" / "***Timeout" / "***Exception"
_CTEST = re.compile(r"Test\s+#\d+:\s+(\S+)\s+\.+\s*(Passed|\*\*\*Failed|\*\*\*Timeout|\*\*\*Exception|\*\*\*Not Run)")
# FIX(jeff-audit d4): four runners printed full per-test evidence that parse_outcomes discarded, so
# the strict grader could never match a FAIL_TO_PASS id and the task scored 0 with a green suite.
# mocha/QUnit "passing: <full title>" and "failing: <title>" (nceas-metacatui-2290).
_MOCHA_WORD = re.compile(r"^\s*(passing|failing|pending):\s+(\S.*?)\s*$")
# QUnit  "TEST DONE: <name> passed=N failed=M"  (openseadragon-2072)
_QUNIT = re.compile(r"^\s*TEST DONE:\s*(.+?)\s+passed=(\d+)\s+failed=(\d+)")
# Catch2 console: "<file>:<line>: <blank> PASSED:/FAILED:" blocks are assertion-level, but the
# section header line names the TEST CASE. Catch2 also prints an explicit per-case summary.
_CATCH2_CASE = re.compile(r"^\s*(?:Scenario|Given|When|Then)?\s*([A-Za-z_][\w :./-]{3,})\s*$")
_CATCH2_OK = re.compile(r"All tests passed \((\d+) assertions? in (\d+) test cases?\)")
_CATCH2_HDR = re.compile(r"^-{10,}\s*$")
# RSpec --format json emits {"examples":[{"full_description":..,"status":"passed"}]}
_RSPEC_EX = re.compile(r'"full_description"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"status"\s*:\s*"(\w+)"')
_RSPEC_EX2 = re.compile(r'"status"\s*:\s*"(\w+)"[^{}]*?"full_description"\s*:\s*"((?:[^"\\]|\\.)*)"')
# dotnet `dotnet test` per-test line: "Passed Namespace.Class.Method [12 ms]" (NOT the "Passed! - …"
# summary — the required whitespace after the verb excludes "Passed!"/"Failed!").
_DOTNET_TC = re.compile(r"^\s*(Passed|Failed|Skipped)\s+(\S+)")
# Maven/Gradle surefire aggregate (per test-class) + failing test method lines
_SUREFIRE = re.compile(r"Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+)(?:,\s*Skipped:\s*(\d+))?", re.I)
_MVN_ERRLINE = re.compile(r"^\[ERROR\]\s+(\S+?)[:. ]", re.M)
# JUnit / xUnit XML <testcase> — emitted by gradle (TEST-*.xml catted to stdout), phpunit
# (--log-junit), jest-junit, mocha-junit, dotnet trx-to-junit, etc. A passing case has no
# <failure>/<error> child; <skipped/> is a skip. This is the per-test signal for JVM/JS/PHP
# runners that do NOT print each passing method on stdout, so grade.py can require every
# FAIL_TO_PASS method OBSERVED as passed rather than trusting a forgeable aggregate count.
_JUNIT_TC = re.compile(r'<testcase\b([^>]*?)(?:/>|>(.*?)</testcase\s*>)', re.S | re.I)
# gradle `testLogging { events "passed","failed","skipped" }` per-test line:
#   "com.foo.BarTest > testBaz PASSED"  (also "> testBaz() PASSED")
# FIX(jeff-audit d4): `^\s*` let this span a NEWLINE (\s matches \n), so any line followed by a line
# beginning with `>` and ending in PASSED registered a passing test — a two-line forgery. Anchored to
# horizontal whitespace only.
_GRADLE_TL = re.compile(r"^[ \t]*(\S[^>\n]*?)[ \t]+>[ \t]+(\S[^>\n]*?)[ \t]+(PASSED|FAILED|SKIPPED)[ \t]*$", re.M)
# FIX(jeff-audit d4): JS runners' STRUCTURED json reporters (built into jest/vitest/mocha — no extra
# package, works offline). Previously only their free-text `✓ title` verbose lines were available,
# which parse_outcomes() deliberately does not accept, so every JS task with a non-empty F2P
# fail-closed to reward 0 (systemic verifier false negative across ~1.1k delivery-4 tasks).
#   jest/vitest --json  ->  {"title":"...","status":"passed"|"failed"|"pending", ...}
#   mocha --reporter json -> {"passes":[{"fullTitle":"..."}],"failures":[...],"pending":[...]}
_JS_JSON_AR = re.compile(r'"(?:fullName|title)"\s*:\s*"((?:[^"\\]|\\.)*)"'
                         r'(?:(?!"(?:fullName|title)")[\s\S]){0,400}?'
                         r'"status"\s*:\s*"(passed|failed|pending|skipped|todo)"')
# FIX(js-chain): jest/vitest --json emit `"fullName":..,"title":..,"status":..` per
# assertionResult. _JS_JSON_AR's tempered gap forbids ANY intervening fullName/title, so on that
# (very common) key order the fullName match died and only the bare `title` was registered -
# the describe chain that configured ids carry was lost and the task fail-closed.
_JS_JSON_FULLNAME = re.compile(r'"fullName"\s*:\s*"((?:[^"\\]|\\.)*)"')
_JS_JSON_STATUS = re.compile(r'"status"\s*:\s*"(passed|failed|pending|skipped|todo)"')
_JS_JSON_MOCHA_SEC = re.compile(r'"(passes|failures|pending)"\s*:\s*\[([\s\S]*?)\]\s*(?=,\s*"|\s*})')
# A candidate top-level JSON document in mixed console output: from a line-initial `{` to the
# line-initial `}` that closes it. Used to parse mocha/jest reports structurally instead of
# regex-slicing their arrays, which broke on any test title containing a bracket.
_JSON_DOC = re.compile(r"(?m)^\{[\s\S]*?^\}", re.M)
_JS_JSON_FULLTITLE = re.compile(r'"fullTitle"\s*:\s*"((?:[^"\\]|\\.)*)"')
# FIX(jeff-audit d4): googletest per-test lines. `[ RUN ]` / `[       OK ] suite.test (0 ms)` /
# `[  FAILED  ] suite.test` is gtest's OWN structured per-test report (not a name mention), and
# without it every gtest task fail-closed with an unparseable output (116 tasks in the final run).
# FIX(jeff-audit d4): unanchored - a test binary's own unflushed stdout can prefix the line.
_GTEST = re.compile(r"\[\s*(OK|FAILED)\s*\]\s+(\S+?)(?:\s+\(\d+\s*ms\))?\s*$", re.M)
# mocha/jasmine/node:test spec reporters mark each test with a tick or cross followed by its title.
# The marker is emitted by the runner per test, so it is a per-test outcome, not free text. ANSI is
# already stripped before parsing. Only used when no richer structured format is present.
# `[0.41ms]` / `[12 ms]` bracket durations (vitest) - `(N ms)` is handled in the tick regex
# vitest also prints a BARE trailing duration (`should set a value with ttl 153ms`), which the
# bracket/paren strippers miss - it then became part of the id and could never match.
_DUR_BARE = re.compile(r"\s+\d+(?:\.\d+)?\s*(?:ms|s)$")
_DUR_BRACKET = re.compile(r"\s*\[(?:\s*[\d.]+\s*[a-z]{1,2})+\s*\]\s*$")
# `src/react/index.test.tsx  (2 tests) 31ms` - a per-FILE aggregate, not a test
_FILE_AGG = re.compile(r"^\S+\.[a-z]{2,4}\s*\(\d+\s+tests?\)")
# a leading `src/x.test.ts` or `|pkg|` token that the configured id does not carry
_PATHY_TOK = re.compile(r"^(\|[^|]+\||\S+\.[a-z]{2,4}|\S+/\S+)$")
_NOISE_HEAD = re.compile(r"^(?:[>$]|at\s|[-=_*]{3,}|https?://)|(?:\S+:\d+(?::\d+)?$)|[{};]\s*$")
# FIX(js-chain): `bun test` marks every test with `(pass)/(fail)/(skip)/(todo) <chain > leaf> [1.2ms]`
# - its OWN per-test report. Without it a bun suite produced no per-test outcome at all.
_BUN_TEST = re.compile(r"^\s*\((pass|fail|skip|todo)\)\s+(\S.*?)\s*$", re.M)
_TICK_OK = re.compile(r"^[.\s]*(?:\d+\)\s*)?[✔✓√]\s+(\S.*?)(?:\s+\(\d+(?:\.\d+)?\s*(?:ms|s|us|ns)\))?\s*$", re.M)
_TICK_BAD = re.compile(r"^[.\s]*(?:\d+\)\s*)?[✗✖×✘]\s+(\S.*?)(?:\s+\(\d+(?:\.\d+)?\s*(?:ms|s|us|ns)\))?\s*$", re.M)
# FIX(jeff-audit d4): custom reporters that append the verdict to the test title, e.g.
# `Modals validates and returns proper hash parameters PASSED`. The status word is the runner's own
# per-test verdict; require it at end-of-line and reject lines that look like prose/summaries so a
# sentence mentioning a test name can never be mistaken for a result.
_TRAILING_STATUS = re.compile(
    r"^[ \t]{0,8}(?![\[#>*+-])([^\s#>][^\n]{3,180}?)[ \t]+(PASSED|FAILED|SKIPPED|PENDING)[ \t]*$", re.M)


def _xml_attr(attr, s):
    m = re.search(r'\b%s\s*=\s*"([^"]*)"' % attr, s) or re.search(r"\b%s\s*=\s*'([^']*)'" % attr, s)
    if not m:
        return None
    # FIX(jeff-audit d4): JUnit/xunit attributes are XML-escaped, and mocha-xunit DOUBLE-escapes, so
    # `should have name "SwitchCase"` was emitted as `... &amp;#x22;SwitchCase&amp;#x22;` and never
    # matched the configured id. Unescape iteratively until stable.
    v = m.group(1)
    for _ in range(3):
        u = _html.unescape(v)
        if u == v:
            break
        v = u
    return v


_GO = re.compile(r"^(=== RUN|--- (PASS|FAIL|SKIP)|ok\s+\S|FAIL\s+\S|\"Action\":\")", re.M)
_MAVEN = re.compile(r"\bmaven\b|surefire|Tests run:|BUILD SUCCESS|BUILD FAILURE|\[INFO\] Running ", re.I)
# JS/TS runners (jest/vitest/mocha/jasmine/ava/tap/node:test) emit test NAMES as free-text `it()`
# descriptions (spaces, not node ids), so per-test id matching is unreliable — grade on the summary
# aggregate instead: tests must have RUN, none may FAIL, and no F2P may appear on a failing line.
_JS = re.compile(r"\b(jest|vitest|mocha|jasmine|\bava\b|node:test|tap-parser|PHPUnit|rspec)\b"
                 r"|^\s*\d+ (passing|failing)\b|Tests?:\s+\d|Test Files\s+\d|# (pass|fail) \d"
                 r"|^OK \(\d+ tests?|\d+ examples?, \d+ (failure|error)|(Passed|Failed)! - Failed:", re.M | re.I)


def _is_fail_line(ln):
    if _PASS_MARK.search(ln):  # explicit per-test PASS marker -> not a failure (fail-word is in the name)
        return False
    if not _FAIL_MARK.search(ln):
        return False
    return bool(_FAIL_MARK.search(_JSON_FALSY_FAIL.sub("", ln)))


def _norm(name):
    s = re.sub(r"^\(\s*\d+\s*/\s*\d+\s*\)\s*", "", str(name)).strip()
    # strip a trailing empty arg-list so a JVM F2P id `Cls::testFoo()` matches the XML `name="testFoo"`
    s = re.sub(r"\(\s*\)$", "", s).strip()
    return s


def _tokens(name):
    n = _norm(name)
    toks = []
    if n:
        toks.append(n)
        last = n.split("::")[-1].strip()
        if last and last != n:
            toks.append(last)
        tail = last.split()[-1] if last.split() else last
        if tail and tail not in toks:
            toks.append(tail)
    return [t for t in toks if len(t) >= 4]


def _json_unescape(s):
    """Decode JSON string escapes in a `go test -json` Test field: Go escapes `<`/`>`/`&` as
    \\u003c/\\u003e/\\u0026, so the raw regex capture (`factor_of_\\u003c=_1`) will not match a
    FAIL_TO_PASS id that carries the literal `<=`. Decoding restores the real subtest name."""
    if "\\" not in s:
        return s
    try:
        return json.loads('"' + s + '"')
    except Exception:
        return s


def parse_outcomes(output, lines):
    """{test-identifier: PASSED|FAILED|ERROR|SKIPPED} across all recognized frameworks."""
    node = {}

    def put(k, v, override=True):
        if not k:
            return
        if override or k not in node:
            node[k] = v

    for ln in lines:
        m = _PYTEST.match(ln)
        if m:
            put(m.group(1) or m.group(4), (m.group(2) or m.group(3)).upper())
        m = _GO_V.match(ln)
        if m:
            put(m.group(2), {"PASS": "PASSED", "FAIL": "FAILED", "SKIP": "SKIPPED"}[m.group(1)])
        m = _NEXTEST.match(ln)
        if m:
            _st = {"PASS": "PASSED", "PASSED": "PASSED", "FAIL": "FAILED",
                   "FAILED": "FAILED", "SKIP": "SKIPPED", "SKIPPED": "SKIPPED"}[m.group(1)]
            _rest = m.group(2).strip()
            # the whole remainder is the id for runners whose names contain spaces (rspec, mocha)
            put(_rest, _st)
            _parts = _rest.split()
            if len(_parts) == 2:
                # cargo-nextest `<binary> <test>`: register the bare test too, both forms are used
                # NOTE: %-format, not an f-string - this grader must parse on old container pythons.
                put(_parts[1], _st, override=False)
        m = _TAP.match(ln)
        if m:
            _nm = _TAP_STRIP.sub("", m.group(2)).strip()
            if _nm and not _nm.lower().startswith(("tests ", "# ")):
                put(_nm, "PASSED" if m.group(1) == "ok" else "FAILED")
        m = _LIBTEST.match(ln)
        if m:
            put(m.group(1), {"ok": "PASSED", "FAILED": "FAILED", "ignored": "SKIPPED"}[m.group(2)])
        m = _DOTNET_TC.match(ln)
        if m:
            put(m.group(2), {"Passed": "PASSED", "Failed": "FAILED", "Skipped": "SKIPPED"}[m.group(1)])
    for m in _GO_JSON_AT.finditer(output):
        put(_json_unescape(m.group(2)), {"pass": "PASSED", "fail": "FAILED", "skip": "SKIPPED"}[m.group(1)])
    for m in _GO_JSON_TA.finditer(output):
        put(_json_unescape(m.group(1)), {"pass": "PASSED", "fail": "FAILED", "skip": "SKIPPED"}[m.group(2)], override=False)
    # FIX(jeff-audit d4): `go test -json` carries the PACKAGE alongside the test name, but only the
    # bare name was recorded. Two packages routinely share a test name (Go's `Test` entrypoint is
    # the common case), so when the graded package failed to BUILD -- `FAIL <pkg> [build failed]`,
    # no outcomes at all -- a same-named test in a sibling package supplied a PASSED under the bare
    # key and an empty submission scored 1 (tsuru-tsuru-2636). Record the qualified id as well so
    # the two can be told apart; _f2p_candidates then refuses the cross-package match.
    for _ln in lines:
        _l = _ln.strip()
        if not (_l.startswith("{") and '"Action"' in _l and '"Test"' in _l):
            continue
        try:
            _o = json.loads(_l)
        except Exception:
            continue
        _a = str(_o.get("Action", "")).lower()
        _t, _pk = _o.get("Test"), _o.get("Package")
        if _t and _pk and _a in ("pass", "fail", "skip"):
            put(str(_pk) + "::" + str(_t),
                {"pass": "PASSED", "fail": "FAILED", "skip": "SKIPPED"}[_a])
            # Once the package-qualified id is recorded, the AMBIGUOUS bare name must go: it is the
            # only thing that let a passing `Test` in one package satisfy a FAIL_TO_PASS entry for
            # a different package's `Test`. Dropping it here (rather than filtering at match time)
            # keeps runners that legitimately print only a bare name unaffected.
            node.pop(str(_t), None)
    for m in _CTEST.finditer(output):
        put(m.group(1), "PASSED" if m.group(2) == "Passed" else "FAILED")
    # FIX(jeff-audit d4): mocha/QUnit word form, QUnit TEST DONE, and RSpec --format json. All three
    # print complete per-test evidence that was previously dropped, leaving the grader with nothing
    # to match and forcing reward 0 on suites that were entirely green.
    for ln in lines:
        m = _MOCHA_WORD.match(ln)
        if m:
            put(m.group(2).strip(),
                {"passing": "PASSED", "failing": "FAILED", "pending": "SKIPPED"}[m.group(1)])
        m = _QUNIT.match(ln)
        if m:
            put(m.group(1).strip(), "FAILED" if int(m.group(3)) else "PASSED")
    for rx, swap in ((_RSPEC_EX, False), (_RSPEC_EX2, True)):
        for m in rx.finditer(output):
            _name, _st = (m.group(2), m.group(1)) if swap else (m.group(1), m.group(2))
            try:
                _name = _json_unescape(_name)
            except Exception:
                pass
            _s = {"passed": "PASSED", "failed": "FAILED",
                  "pending": "SKIPPED"}.get(str(_st).lower())
            if _s:
                put(_name.strip(), _s)
    # Catch2 console output names each TEST CASE on the line under a dashed rule; the final summary
    # states whether every case passed. Only the all-passed form is unambiguous, so record the named
    # cases as PASSED just in that case -- a failure block is already reported by the FAILED: lines.
    if _CATCH2_OK.search(output):
        for i, ln in enumerate(lines):
            if _CATCH2_HDR.match(ln) and i + 1 < len(lines):
                nxt = lines[i + 1].rstrip()
                if nxt and not nxt.startswith(("-", "=", "/", " ")) and len(nxt) > 3:
                    put(nxt.strip(), "PASSED", override=False)
    # FIX(jeff-audit d4): jest/vitest --json assertionResults + mocha --reporter json sections.
    _JSMAP = {"passed": "PASSED", "failed": "FAILED",
              "pending": "SKIPPED", "skipped": "SKIPPED", "todo": "SKIPPED"}
    for m in _JS_JSON_AR.finditer(output):
        nm = _json_unescape(m.group(1)).strip()
        put(nm, _JSMAP[m.group(2)])
        if "::" not in nm and " " in nm:
            # FIX(jeff-audit d4): this last-word alias is AMBIGUOUS by construction -- dozens of JS
            # titles end in the same word ("button", "changed", "strings"), and the derivation baked
            # those bare tokens into FAIL_TO_PASS on 392 tasks (3,191 keys). With first-wins
            # (override=False) a PASSING sibling claimed the alias and a genuinely FAILING test was
            # then certified by it, so an empty submission could score. Make the alias
            # FAILURE-DOMINANT: once any test sharing the last word failed, the alias is FAILED and
            # can no longer vouch for anything. An unambiguous alias is unaffected.
            _al = nm.rsplit(" ", 1)[-1]
            _st = _JSMAP[m.group(2)]
            put(_al, _st, override=(_st == "FAILED" or node.get(_al) != "FAILED"))
    for m in _JS_JSON_FULLNAME.finditer(output):
        # linear window scan (NOT a tempered regex - that backtracks quadratically on
        # multi-MB reporter dumps): the status of this assertionResult must appear within
        # the next 600 chars and before the NEXT "fullName" key.
        _w = output[m.end():m.end() + 600]
        _nxt = _w.find('"fullName"')
        if _nxt >= 0:
            _w = _w[:_nxt]
        _sm = _JS_JSON_STATUS.search(_w)
        if not _sm:
            continue
        nm = _json_unescape(m.group(1)).strip()
        if nm:
            put(nm, _JSMAP[_sm.group(1)], override=(_JSMAP[_sm.group(1)] == "FAILED"))
    # FIX(jeff-audit d4): parse the mocha JSON report STRUCTURALLY. The section regex bounded each
    # array with a non-greedy `[\s\S]*?` and a `]` lookahead, so any test title ENDING in a bracket
    # ("... handles opts[0]") closed the array early and every later test became invisible. Measured
    # on recorded output: 194 tasks saw under 90% of their titles, worst
    # yannickcr-eslint-plugin-react-31 at 2 of 532 and gajus-eslint-plugin-jsdoc-1489 at 96 of 5,350.
    # The derivation could then only ever see a prefix of the suite, which is a direct cause of the
    # "F2P unrelated to test.patch" residue. Walk the real JSON; fall back to the old scan only if
    # nothing parses.
    _mocha_hit = False
    if '"fullTitle"' in output:
        for _cand in _JSON_DOC.finditer(output):
            _txt = _cand.group(0)
            try:
                _doc = json.loads(_txt)
            except Exception:
                continue
            if not isinstance(_doc, dict):
                continue
            for _sec, _oc in (("passes", "PASSED"), ("failures", "FAILED"), ("pending", "SKIPPED")):
                _arr = _doc.get(_sec)
                if not isinstance(_arr, list):
                    continue
                for _e in _arr:
                    if not isinstance(_e, dict):
                        continue
                    _nm = str(_e.get("fullTitle") or _e.get("title") or "").strip()
                    if _nm:
                        # a failure must never be overwritten by a same-named pass
                        put(_nm, _oc, override=(_oc == "FAILED" or node.get(_nm) != "FAILED"))
                        _mocha_hit = True
    if not _mocha_hit:
        for sec in _JS_JSON_MOCHA_SEC.finditer(output):
            oc = {"passes": "PASSED", "failures": "FAILED", "pending": "SKIPPED"}[sec.group(1)]
            for t in _JS_JSON_FULLTITLE.finditer(sec.group(2)):
                put(_json_unescape(t.group(1)).strip(), oc)
    # FIX(jeff-audit d4): additional green-but-unreadable reporters. All override=False so any
    # richer structured format parsed earlier always wins.
    for m in _FOUNDRY.finditer(output):
        put(m.group(2).strip(), "PASSED" if m.group(1) == "PASS" else "FAILED")
    for m in _XCTEST.finditer(output):
        nm = m.group(1).strip()
        st = "PASSED" if m.group(2) == "passed" else "FAILED"
        put(nm, st)
        if "." in nm:
            put(nm.split(".", 1)[-1], st, override=False)
    for m in _DENO.finditer(output):
        put(m.group(1).strip(), "PASSED" if m.group(2) == "ok" else "FAILED", override=False)
    for m in _SBT.finditer(output):
        put(m.group(1).strip(), "PASSED", override=False)
    for m in _PLAYWRIGHT.finditer(output):
        nm = re.sub(r"^\S+\.[a-z]{2,4}:\d+:\d+\s*[\u203a>]\s*", "", m.group(1).strip())
        put(nm, "PASSED", override=False)
        put(nm.replace(" \u203a ", " ").replace(" > ", " "), "PASSED", override=False)
    for m in _NAME_OK.finditer(output):
        nm = m.group(1).strip()
        if not nm.lower().startswith(("total", "summary", "result", "tests", "suite total")):
            put(nm, "PASSED" if m.group(2) == "OK" else "FAILED", override=False)
    # FIX(jeff-audit d4): googletest
    for m in _GTEST.finditer(output):
        nm = m.group(2)
        put(nm, "PASSED" if m.group(1) == "OK" else "FAILED")
        if "." in nm:
            put(nm.split(".", 1)[-1], "PASSED" if m.group(1) == "OK" else "FAILED", override=False)
    for m in _BUN_TEST.finditer(output):
        _oc = {"pass": "PASSED", "fail": "FAILED",
               "skip": "SKIPPED", "todo": "SKIPPED"}[m.group(1)]
        _bn = _DUR_BRACKET.sub("", m.group(2)).strip()
        if not _bn:
            continue
        put(_bn, _oc, override=(_oc == "FAILED"))
        if " > " in _bn:
            _bp = [x.strip() for x in _bn.split(" > ") if x.strip()]
            put(_bp[-1], _oc, override=False)
    # FIX(jeff-audit d4): spec-reporter tick/cross lines (mocha, jasmine, node:test). Recorded with
    # override=False so any richer structured format already parsed above wins.
    # ---- spec-reporter tick lines (mocha / jest / jasmine / vitest / AVA) ----
    # FIX(jeff-audit d4): register the chain-qualified id as well as the bare leaf. Reporters print
    # the describe chain either inline (vitest `a > b > c`) or as indented headers with only the leaf
    # on the tick line (mocha), while configured ids carry the whole chain - so a bare leaf never
    # matched and the task fail-closed.
    _chain = {}          # indent level -> heading text, for the indented style
    for _ln in lines:
        _st = None
        _mm = _TICK_OK.match(_ln)
        if _mm:
            _st = "PASSED"
        else:
            _mm = _TICK_BAD.match(_ln)
            if _mm:
                _st = "FAILED"
        if _st is None:
            # a non-tick, non-blank line at this indent is a describe heading
            _t = _ln.rstrip()
            if _t.strip() and not _t.lstrip().startswith(("PASS", "FAIL", "Tests:", "Test Suites:")):
                _ind = len(_t) - len(_t.lstrip())
                _head = _t.strip()
                # FIX(js-chain): a describe heading in every JS spec reporter is INDENTED (mocha/jest
                # start at column 2). Column-0 lines are npm/yarn command echoes, warnings and stack
                # frames -- accepting them as headings both prefixed junk onto the reconstructed id
                # and (because a col-0 line deletes every deeper entry) DESTROYED the real chain.
                if _ind >= 2 and not _NOISE_HEAD.search(_head) \
                        and len(_head) < 120 and not _head.endswith((".", ":")):
                    _chain[_ind] = _head
                    for _k in [k for k in _chain if k > _ind]:
                        del _chain[_k]
            continue
        _name = _mm.group(1).strip()
        _name = _DUR_BRACKET.sub("", _name).strip()
        _name = _DUR_BARE.sub("", _name).strip()
        if _FILE_AGG.match(_name):
            continue                      # `src/x.test.tsx  (2 tests) 31ms` is a file total
        put(_name, _st, override=(_st == "FAILED"))
        if " > " in _name:                # vitest inline chain
            _parts = [x.strip() for x in _name.split(" > ") if x.strip()]
            if len(_parts) > 1:
                if _PATHY_TOK.match(_parts[0]):
                    _parts = _parts[1:]   # drop the leading file path / |pkg| token
                put(" ".join(_parts), _st, override=False)
                put(_parts[-1], _st, override=False)
        else:                             # mocha indented style: join the enclosing headings
            _ind = len(_ln) - len(_ln.lstrip())
            _heads = [_chain[k] for k in sorted(_chain) if k < _ind]
            # FIX(js-chain): register EVERY chain SUFFIX, not only the full chain. Configured ids
            # carry the describe chain from the top-level describe down, but the reporter may also
            # print an outer grouping (project/file/package banner) that the id does not include -
            # with only the full chain registered such an id could never match.
            for _i in range(len(_heads)):
                put(" ".join(_heads[_i:] + [_name]), _st, override=False)
    # FIX(jeff-audit d4): `<test title> PASSED` style reporters. override=False so any richer
    # structured format parsed above always wins.
    for m in _TRAILING_STATUS.finditer(output):
        nm = m.group(1).strip()
        if nm.lower().startswith(("tests", "test suites", "total", "summary", "ran ", "results")):
            continue
        put(nm, {"PASSED": "PASSED", "FAILED": "FAILED",
                 "SKIPPED": "SKIPPED", "PENDING": "SKIPPED"}[m.group(2)], override=False)
    # gradle testLogging per-test lines ("Class > method PASSED")
    for m in _GRADLE_TL.finditer(output):
        cls, meth = m.group(1).strip(), re.sub(r"\(\s*\)$", "", m.group(2).strip())
        oc = {"PASSED": "PASSED", "FAILED": "FAILED", "SKIPPED": "SKIPPED"}[m.group(3)]
        put(cls + "::" + meth, oc)
        put(meth, oc, override=False)
    # JUnit / xUnit <testcase> elements (gradle TEST-*.xml, phpunit --log-junit, jest/mocha-junit, trx)
    for m in _JUNIT_TC.finditer(output):
        attrs, body = m.group(1), (m.group(2) or "")
        nm = _xml_attr("name", attrs)
        if not nm:
            continue
        nm = re.sub(r"\(\s*\)$", "", nm.strip())
        cls = _xml_attr("classname", attrs) or _xml_attr("class", attrs)
        if re.search(r"<(failure|error)\b", body, re.I):
            oc = "FAILED"
        elif re.search(r"<skipped\b", body, re.I):
            oc = "SKIPPED"
        else:
            oc = "PASSED"
        if cls:
            put(cls + "::" + nm, oc)
        put(nm, oc, override=False)

    # FIX(jeff-audit d4): pytest-subtests / unittest subTest report the PARENT test as PASSED and
    # emit each failing case separately as `SUBFAILED(...)`. The parent's PASSED was recorded and
    # the failures were invisible, so a task whose graded test failed every subtest still scored 1
    # for an EMPTY submission (wagtail-wagtail-10779 and 29 others: "4 failed, 3 passed" yet
    # reward 1.0). A parent whose subtests failed did not pass; demote it.
    if _SUBFAIL_TOK.search(output):
        _prev_id = None
        for ln in lines:
            _ids = _SUBFAIL_ID.findall(ln)
            if _SUBFAIL_TOK.search(ln):
                _hit = _ids[0] if _ids else _prev_id
                if _hit:
                    for _k in (_hit, _hit.split("::", 1)[-1]):
                        if _k in node and node[_k] == "PASSED":
                            node[_k] = "FAILED"
            _prev_id = _ids[-1] if _ids else _prev_id
    return node


# FIX(js-chain): reporters append a per-test duration to the printed title and some derived
# FAIL_TO_PASS ids captured it (`do not error on restart (110.851378ms)`). A duration is
# run-dependent, so it can never match on a later run - strip it from BOTH sides.
_ID_DUR = re.compile(r"\s*[\(\[]\s*\d+(?:\.\d+)?\s*(?:ms|s|us|\u00b5s|ns)\s*[\)\]]\s*$")

_MK_CACHE = {}


def _match_keys(raw):
    # FIX(jeff-audit d4): memoized. _strict_pertest_ok compares every F2P id against every
    # observed node, so recomputing keys per pair was quadratic - 171s inside grade.py on a
    # 2,938-id task, a real verifier-timeout risk.
    _c = _MK_CACHE.get(raw)
    if _c is not None:
        return _c
    _r = _match_keys_uncached(raw)
    _MK_CACHE[raw] = _r
    return _r


def _match_keys_uncached(raw):
    """Exact-match keys for one test identifier, normalized symmetrically for F2P ids and parsed
    node ids. FIX(jeff-audit d4): the old version split on `::|.|#|/` and took the last segment
    WITHOUT stripping, so
      * `x.test.js:: Error Messages … handles network errors` kept a leading space and could never
        equal the runner-reported name (JS/vitest/jest false negatives),
      * a test TITLE containing `.` or `/` (`handles v1.2 input`, `parses a/b`) was chopped mid-title,
      * xUnit theory args (`Method(policy: Required | ReferenceTypes)`) were split inside the
        parentheses, and
      * pytest parametrized ids (`[ partitioned ]`) differed only by inner whitespace.
    All keys are still EXACT strings (never substrings), so per-test proof stays as strict as before.
    """
    s = _norm(raw)
    if not s:
        return set()
    keys = {s}
    # FIX(js-chain): duration suffix and the ` > ` describe-chain separator are presentation, not
    # identity. Normalise BOTH here so an id derived from one reporter matches the same test reported
    # by another (jest joins the chain with a space, vitest/mocha with ` > `). Still exact strings.
    for _v in (_ID_DUR.sub("", s).strip(), s.replace(" > ", " ")):
        if _v:
            keys.add(_v)
    for _k in list(keys):
        _v = _ID_DUR.sub("", _k.replace(" > ", " ")).strip()
        if _v:
            keys.add(_v)
    # part after the last `::` (the framework's own test name in nearly every runner)
    if "::" in s:
        keys.add(s.split("::")[-1].strip())
    # last dotted/hashed/slashed segment, computed only OUTSIDE parens/brackets so arg lists and
    # parametrized suffixes are never split apart
    for k in list(keys):
        head, sep, tail = k.partition("(")
        bhead, bsep, btail = head.partition("[")
        segs = [x.strip() for x in re.split(r"::|\.|#|/", bhead) if x.strip()]
        if segs:
            base = segs[-1] + (bsep + btail if bsep else "") + (sep + tail if sep else "")
            # FIX(jeff-audit d4): the last segment is only a usable fallback when it NAMES the test.
            # A parameterized GTest id (`Suite/ParamTest.DoesThing/0`) ends in the instantiation
            # INDEX, so every such id collapsed to the key `0` and any other passing `.../0` test
            # satisfied a FAILING FAIL_TO_PASS entry -- and grade.py overrides a nonzero runner exit
            # on that basis. A real test name is never a bare number or a 1-2 character token.
            _lead = segs[-1].strip()
            if _lead and not _lead.isdigit() and len(_lead) > 2:
                keys.add(base.strip())
    # whitespace-collapsed and whitespace-free variants (inner-spacing differences only)
    for k in list(keys):
        keys.add(re.sub(r"\s+", " ", k).strip())
        keys.add(re.sub(r"\s+", "", k))
    return {k for k in keys if k}


_NODE_INDEX_CACHE = {}
_NODE_INDEX_ORDER = []


def _node_index(node_outcome):
    """key -> [node ids]. Built once per outcome set instead of rescanned per F2P id.

    FIX(jeff-audit d4): this used to key the cache on id() ALONE. id() is unique only among LIVE
    objects, so once an outcome dict is freed CPython hands its address to the next one -- and in a
    batch replay loop (many tasks scored in one process) the grader then served a PREVIOUS task's
    index, silently mis-scoring. Harmless in the one-shot verifier, corrupting in any offline
    harness. Hold a reference to the keyed object so its id cannot be recycled while cached, and
    re-verify identity on every hit.
    """
    k = id(node_outcome)
    ent = _NODE_INDEX_CACHE.get(k)
    if ent is not None and ent[0] is node_outcome:
        return ent[1]
    idx = {}
    for nd in node_outcome:
        for key in _match_keys(nd):
            idx.setdefault(key, []).append(nd)
    _NODE_INDEX_CACHE[k] = (node_outcome, idx)
    _NODE_INDEX_ORDER.append(k)
    while len(_NODE_INDEX_ORDER) > 4:
        _NODE_INDEX_CACHE.pop(_NODE_INDEX_ORDER.pop(0), None)
    return idx


def _f2p_candidates(name, node_outcome):
    """Nodes sharing an exact normalized identifier with the F2P name."""
    want = _match_keys(name)
    if not want:
        return []
    idx = _node_index(node_outcome)
    out = []
    for key in want:
        for nd in idx.get(key, ()):
            if nd not in out:
                out.append(nd)
    # FIX(jeff-audit d4): a CONTAINER-QUALIFIED F2P id must not be satisfied by a same-named test
    # from a DIFFERENT container. `_match_keys` deliberately emits the bare leaf as a fallback (many
    # runners print only the leaf), but that fallback let `github.com/tsuru/tsuru/api::Test` match a
    # passing `Test` in .../auth after the api package failed to build -- an empty submission scored
    # 1. Only disambiguate when qualified candidates actually exist, so the leaf-only fallback still
    # works for runners that never print a container.
    # FIX(jeff-audit d4): also disambiguate DOTTED ids (xunit/NUnit `Cls.Method.Should_X`, Java
    # `pkg.Cls.test`). Restricting this to `::` left `Cls.GetItem.Should_Return` satisfiable by a
    # passing `Cls.GetItemAsync.Should_Return`.
    # FIX(jeff-audit d4): identity-alias fail-open. `_match_keys` emits a bare-LEAF fallback key so a
    # runner that prints only the leaf still matches. That fallback also let a DIFFERENT passing test
    # certify a FAILING FAIL_TO_PASS id when the two share a leaf -- `.../project/test.ts.lint` and
    # `.../default/test.ts.lint` both collapse to `lint`, and an EMPTY submission scored 1.0 on the
    # strength of the sibling that still passed (fimbullinter-wotan-230). When the F2P's OWN node is
    # in the candidate set, use only it: the leaf fallback stays available for runners that never
    # print the qualified form, but it can no longer outvote the real observation.
    if len(out) > 1:
        _wn = _norm(str(name))
        # FIX(jeff-audit d4): EXACT self-match must win outright and alone. The earlier version also
        # accepted `_wn.endswith("::" + node)`, which keeps the BARE LEAF in the candidate set -- so
        # when the F2P's own qualified node was PRESENT AND FAILED, a same-named test in a different
        # class still certified it and an empty submission scored 1.0
        # (stripe-stripe-php-989: all 9 Stripe\PromotionCodeTest::* FAILED on nop, reward 1;
        #  neo4j-...-apoc: testPathTraversal[N] FAILED in one @Nested class, PASSED in four siblings).
        # Prefer the exact node; only if there is none fall back to suffix relationships.
        _exact = [nd for nd in out if _norm(str(nd)) == _wn]
        if _exact:
            out = _exact
        else:
            _self = [nd for nd in out
                     if _norm(str(nd)).endswith("/" + _wn) or _norm(str(nd)).endswith("::" + _wn)]
            if _self:
                out = _self
            else:
                _loose = [nd for nd in out
                          if _wn.endswith("/" + _norm(str(nd))) or _wn.endswith("::" + _norm(str(nd)))]
                if _loose:
                    out = _loose
    # Only disambiguate when EVERY candidate is container-qualified. If a bare-name candidate is
    # also present the runner simply prints unqualified ids (jest/mocha titles), and discarding it
    # would reject a legitimate match -- which is what broke nrwl-nx-33349 and ceramicstudio-js-idx-4.
    _s = str(name)
    if ("::" in _s or _DOTTED_ID.match(_s)) and out:
        _qual = [nd for nd in out if "::" in str(nd) or _DOTTED_ID.match(str(nd))]
        if len(_qual) == len(out):
            _wc = _container_tail(name)
            if _wc:
                _same = [nd for nd in _qual if _container_tail(nd) == _wc]
                return _same if _same else []
    return out


def _container_tail(ident):
    """Last meaningful segment of a test id's container (`a/b/pkg::Test` -> `pkg`,
    `tests.mod.ClassName::test_x` -> `ClassName`, `a/b/file.py::Cls::test_x` -> `Cls`)."""
    s = _norm(str(ident))
    if "::" in s:
        head = s.rsplit("::", 1)[0]
    elif s.count(".") >= 2:
        head = s.rsplit(".", 1)[0]
    else:
        return ""
    segs = [x.strip() for x in re.split(r"::|/|\.", head) if x.strip()]
    # a bare file extension segment (`py`, `ts`, `go`) is not a container name
    while segs and len(segs[-1]) <= 4 and segs[-1].isalpha() and len(segs) > 1:
        if segs[-1].lower() in ("py", "ts", "js", "go", "rs", "tsx", "jsx", "java", "cs", "rb", "php"):
            segs.pop()
        else:
            break
    return segs[-1] if segs else ""


def _strict_pertest_ok(f2p, node_outcome):
    """Fix G: every configured FAIL_TO_PASS test must be OBSERVED — via the framework's STRUCTURED
    per-test output (parse_outcomes) — as run AND PASSED. A test with no matching per-test outcome
    (never observed run) or whose matching outcome is not PASSED => reward 0. There is deliberately
    NO "name visible on a non-failure line" fallback: a bare grep-visible name is not proof the
    framework executed that test and reported it PASSED."""
    for name in f2p:
        cands = _f2p_candidates(name, node_outcome)
        if not cands or not any(node_outcome[c] == "PASSED" for c in cands):
            return False
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stdout", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--exit-code", type=int, required=True)
    p.add_argument("--reward-out", required=True)
    args = p.parse_args()

    with open(args.config) as f:
        config = json.load(f)
    f2p = config.get("FAIL_TO_PASS", []) or []
    with open(args.stdout, errors="replace") as f:
        output = _ANSI.sub("", f.read())
    lines = output.splitlines()

    reward = 1 if args.exit_code == 0 else 0

    # FIX(jeff-audit d4): the aggregate exit code must not be the ONLY path to reward 1. A suite that
    # also contains unrelated pre-existing failures exits nonzero, which zeroed a correct submission
    # even when every graded test passed (a verifier false negative, and the reason a number of
    # oracle runs scored 0 on green FAIL_TO_PASS sets). Per-test structured observation is STRONGER
    # evidence than the exit code and is what the SWE-bench contract actually specifies, so honour it:
    # every configured FAIL_TO_PASS id must be observed PASSED in the framework's own structured
    # output. This cannot be forged by exiting 0 — the ids still have to appear as passed.
    if reward == 0 and f2p:
        _node = parse_outcomes(output, lines)
        if _node and _strict_pertest_ok(f2p, _node):
            reward = 1

    # FIX(jeff-audit d4): only veto when NOTHING was observed. A multi-module build that logs
    # "No tests to run." for one module must not zero a task whose F2P ids all passed.
    if reward == 1 and _ZERO_RUN.search(output) and not parse_outcomes(output, lines):
        reward = 0

    if reward == 1 and not f2p:
        # HARDEN(verifier-nop) FIX C: an empty/missing FAIL_TO_PASS cannot certify the task is
        # fix-dependent, so it must FAIL CLOSED (0) rather than fall through to the bare, forgeable
        # exit code — a no-op that merely exits 0 no longer scores 1. Such a task must be dropped at
        # convert time, never graded by exit code.
        reward = 0

    if reward == 1 and f2p:
        # Fix G (rewardhack/grader verdicts): reward ONLY when EVERY configured FAIL_TO_PASS test is
        # individually OBSERVED, in the framework's STRUCTURED per-test output, as run AND PASSED.
        # parse_outcomes() extracts per-test verdicts from every framework whose output carries a
        # structured per-test signal — pytest/unittest -v, `go test -v`/`-json`, cargo libtest/nextest,
        # ctest, `dotnet test` detailed (`Passed <name>`), gradle testLogging, and JUnit/xUnit/trx XML
        # (jest-junit, mocha-junit, phpunit --log-junit, gradle TEST-*.xml). The converter side
        # (force_perframework_verbose) forces each runner to emit that per-test signal.
        #
        # There is deliberately NO fallback:
        #   * NO aggregate pass-count (old _js_aggregate / _jvm_aggregate) — a forged "N passing" /
        #     "Tests run: N, Failures: 0" / "Passed! - Failed: 0" summary no longer scores 1;
        #   * NO synthetic-id fallback (old f2p_synthetic) — a converter placeholder id that carries
        #     no observable per-test signal cannot be enforced, so it must fail closed, not aggregate;
        #   * NO "name visible on a non-failure line" fallback (old _names_observed_ok / _lenient_ok) —
        #     a grep-visible name is not proof the framework ran that test and reported it PASSED.
        # If a task's real suite genuinely cannot emit a structured per-test signal offline, the task
        # must be DROPPED at convert time, never graded by a forgeable aggregate.
        node_outcome = parse_outcomes(output, lines)
        if not node_outcome or not _strict_pertest_ok(f2p, node_outcome):
            reward = 0

    # COLLECTED-BUT-NOT-EXECUTED guard (pytest): "collected N items" but zero tests actually ran.
    # Gate strictly on the pytest collection marker so it never misfires on another framework whose
    # node ids merely contain "::" (e.g. cargo-nextest emits `PASS [t] crate mod::test`, not PASSED).
    # Any parsed per-test outcome (pytest/go/rust/ctest) counts as executed.
    if reward == 1 and f2p:
        pytest_collected = bool(re.search(r"collected\s+\d+\s+item", output))
        executed = bool(parse_outcomes(output, lines)) or any(_VERBOSE_MARK.search(ln) for ln in lines)
        if pytest_collected and not executed:
            reward = 0

    with open(args.reward_out, "w") as f:
        f.write(str(reward) + "\n")


if __name__ == "__main__":
    main()
