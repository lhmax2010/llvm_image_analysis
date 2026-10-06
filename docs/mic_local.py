#!/usr/bin/env python3
"""Local mic entry: load global -c before the original PluginMgr is imported.
The unmodified mic 2.1.3 parser accepts -c only on create subcommands, so forward
it there after applying the site configuration early. No privilege escalation.
"""
import argparse
import configparser
import os
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
MIC = ROOT / 'work/tools/usr/bin/mic'


def prepare(argv):
    """Consume only global config; preserve the remaining original mic argv."""
    boundary = next((i for i, arg in enumerate(argv)
                     if arg in ('cr', 'create', 'ch', 'chroot')), len(argv))
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument('-c', '--config')
    opts, prefix = parser.parse_known_args(argv[:boundary])
    forwarded = prefix + argv[boundary:]
    if opts.config is None:
        return forwarded, None
    if boundary == len(argv) or argv[boundary] not in ('cr', 'create'):
        parser.error('global -c requires cr/create and its image subcommand')
    if any(arg in ('-c', '--config') or arg.startswith('--config=')
           for arg in argv[boundary:]):
        parser.error('specify -c once, before cr/create')
    config = Path(opts.config).expanduser().resolve()
    if not config.is_file():
        parser.error(f'config file does not exist: {config}')
    site = configparser.ConfigParser()
    with config.open() as stream:
        site.read_file(stream)
    if not site.has_option('common', 'plugin_dir'):
        parser.error('config requires [common] plugin_dir')
    plugins = Path(site.get('common', 'plugin_dir')).expanduser().resolve()
    if not (plugins / 'imager').is_dir():
        parser.error(f'local imager plugin directory does not exist: {plugins / "imager"}')
    os.environ['MIC_PLUGIN_DIR'] = str(plugins)
    # Forward the config after the image subcommand (auto/loop/fs/etc.).
    insert = len(prefix) + 2
    forwarded[insert:insert] = ['-c', str(config)]
    return forwarded, config


def main(argv=None):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT / 'work/tools/usr/lib/python3/dist-packages'))
    forwarded, config = prepare(list(sys.argv[1:] if argv is None else argv))
    if config is not None:
        # conf's default import may warn about /etc/mic/mic.conf; MIC_PLUGIN_DIR
        # already points locally. Explicit config must load before PluginMgr.
        from mic.conf import configmgr
        configmgr._siteconf = str(config)
    sys.argv = [str(MIC), *forwarded]
    runpy.run_path(str(MIC), run_name='__main__')


if __name__ == '__main__':
    main()
