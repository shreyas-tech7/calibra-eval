"""The `calibra` command."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .readme import update
from .report import html_page, load_results, pr_comment, terminal_report
from .suite import load_suite, run_suite, write_json


def cmd_run(args) -> int:
    mode = "record" if args.record else "replay"
    for suite in args.suites:
        cfg, _ = load_suite(suite)
        res = run_suite(suite, mode, args.seed, args.workers, args.prices)
        out = Path(args.out) / f"{cfg['name']}.json"
        write_json(res, out)
        res["_file"] = out.as_posix()
        print(terminal_report([res]))
        print(f"wrote {out}")
    return 0


def cmd_report(args) -> int:
    results = load_results(args.results)
    print(terminal_report(results))
    if args.html:
        Path(args.html).write_text(html_page(results), encoding="utf-8")
        print(f"wrote {args.html}")
    return 0


def cmd_readme(args) -> int:
    same = update(args.readme, args.results, check=args.check)
    if args.check:
        print("README matches the result files" if same else "README is out of date: run `calibra readme`")
        return 0 if same else 1
    print("README up to date" if same else "README updated")
    return 0


def cmd_pr_comment(args) -> int:
    body = pr_comment(load_results(args.results))
    if args.out:
        Path(args.out).write_text(body, encoding="utf-8")
    else:
        sys.stdout.write(body)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="calibra", description=__doc__)
    p.add_argument("--version", action="version", version=f"calibra-eval {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run suites (replay from fixtures by default)")
    r.add_argument("suites", nargs="+", help="suite TOML files")
    r.add_argument("--record", action="store_true", help="call the model for missing fixtures")
    r.add_argument("--out", default="results", help="folder for result JSON")
    r.add_argument("--seed", type=int, default=None)
    r.add_argument("--workers", type=int, default=None)
    r.add_argument("--prices", default=None, help="optional price table TOML")
    r.set_defaults(fn=cmd_run)

    rep = sub.add_parser("report", help="print tables from result files, optionally write HTML")
    rep.add_argument("--results", default="results")
    rep.add_argument("--html", default=None)
    rep.set_defaults(fn=cmd_report)

    rd = sub.add_parser("readme", help="write the README tables from the result files")
    rd.add_argument("--readme", default="README.md")
    rd.add_argument("--results", default="results")
    rd.add_argument("--check", action="store_true", help="exit 1 if the README is out of date")
    rd.set_defaults(fn=cmd_readme)

    pc = sub.add_parser("pr-comment", help="render the pull request comment body")
    pc.add_argument("--results", default="results")
    pc.add_argument("--out", default=None)
    pc.set_defaults(fn=cmd_pr_comment)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
