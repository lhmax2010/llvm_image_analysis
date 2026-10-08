#!/usr/bin/python3 -tt
#
# Copyright (c) 2009, 2010, 2011 Intel, Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; version 2 of the License
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc., 59
# Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import os
import sys
import glob
import re
import shutil
import subprocess
import tempfile
import ctypes

from mic import bootstrap, msger, kickstart
from mic.conf import configmgr
from mic.utils import errors, proxy
from mic.utils.fs_related import find_binary_path, makedirs, load_module
from mic.chroot import setup_chrootenv, cleanup_chrootenv, ELF_arch

from mic.plugin import pluginmgr

_libc = ctypes.cdll.LoadLibrary(None)
_errno = ctypes.c_int.in_dll(_libc, "errno")
_libc.personality.argtypes = [ctypes.c_ulong]
_libc.personality.restype = ctypes.c_int
_libc.unshare.argtypes = [ctypes.c_int,]
_libc.unshare.restype = ctypes.c_int

expath = lambda p: os.path.abspath(os.path.expanduser(p))

PER_LINUX32=0x0008
PER_LINUX=0x0000
personality_defs = {
    'x86_64': PER_LINUX, 'ppc64': PER_LINUX, 'sparc64': PER_LINUX,
    'i386': PER_LINUX32, 'i586': PER_LINUX32, 'i686': PER_LINUX32,
    'ppc': PER_LINUX32, 'sparc': PER_LINUX32, 'sparcv9': PER_LINUX32,
    'ia64' : PER_LINUX, 'alpha' : PER_LINUX,
    's390' : PER_LINUX32, 's390x' : PER_LINUX,
}

def condPersonality(per=None):
    if per is None or per in ('noarch',):
        return
    if personality_defs.get(per, None) is None:
        return
    res = _libc.personality(personality_defs[per])
    if res == -1:
        raise OSError(_errno.value, os.strerror(_errno.value))

def inbootstrap():
    if os.path.exists(os.path.join("/", ".chroot.lock")):
        return True
    return (os.stat("/").st_ino != 2)

# check python version in mic-bootstrap
def mic_py2_in_mic_bootstrap(binpth_in_micbootstrap):
    #Check /usr/bin/mic file in mic bootstrap, if there is #!/usr/bin/python2 -tt, mean it is python2.x version.
    #For python2.x version, the first line of /usr/bin/mic in mic-bootstrap is: #!/bin/python -tt
    #For python3.x version, the first line of /usr/bin/mic in mic-bootstrap is: #!/bin/python3 -tt
    with open(binpth_in_micbootstrap, 'r') as mic_bin:
        first_line = mic_bin.readline()

    msger.debug("first line of /usr/bin/mic in mic bootstrap: %s" % first_line)
    if (first_line.find('python3') == -1):
        return True
    return False

# Provide '%runscript_out_bootstrap' section for kickstart, and runscript_out_bootstrap can
# be run on local PC after image created. The default interpreter is /bin/sh,
# use '--interpreter' to specify interpreter ('%runscript_out_bootstrap --interpreter=/bin/bash')
def run_scripts_out_bootstrap(ks, rundir, env=None):
    if kickstart.get_out_bootstarp_scripts(ks)==[]:
        return

    msger.info("Running scripts out bootstrap ...")
    for s in kickstart.get_out_bootstarp_scripts(ks):
        (fd, path) = tempfile.mkstemp(prefix="ks-runscript-out-bootstrap-")
        s.script = s.script.replace("\r", "")
        os.write(fd, s.script.encode())
        if s.interp == '/bin/sh' or s.interp == '/bin/bash':
            os.write(fd, '\n'.encode())
            os.write(fd, 'exit 0\n'.encode())
        os.close(fd)
        os.chmod(path, 0o700)

        oldoutdir = os.getcwd()
        if os.path.exists(rundir):
            os.chdir(rundir)
        try:
            try:
                p = subprocess.Popen([s.interp, path],
                                     env = env,
                                     stdout = subprocess.PIPE,
                                     stderr = subprocess.STDOUT)
                while p.poll() == None:
                    msger.info(p.stdout.readline().strip().decode())
                if p.returncode != 0:
                    raise errors.CreatorError("Failed to execute script out bootstrap "
                                              "with '%s'" % (s.interp))
            except OSError as msg:
                    raise errors.CreatorError("Failed to execute script out bootstrap "
                                              "with '%s' : %s" % (s.interp, msg))
        finally:
            os.chdir(oldoutdir)
            os.unlink(path)

def bootstrap_mic(argv=None):
    def mychroot():
        os.chroot(rootdir)
        os.chdir(cwd)

    # by default, sys.argv is used to run mic in bootstrap
    if not argv:
        argv = sys.argv
    if argv[0] not in ('/usr/bin/mic', 'mic'):
        argv[0] = '/usr/bin/mic'

    cropts = configmgr.create
    bsopts = configmgr.bootstrap
    distro = bsopts['distro_name'].lower()

    rootdir = bsopts['rootdir']
    pkglist = bsopts['packages']
    cwd = os.getcwd()

    # create bootstrap and run mic in bootstrap
    bsenv = bootstrap.Bootstrap(rootdir, distro, cropts['arch'])
    bsenv.logfile = cropts['logfile']
    # rootdir is regenerated as a temp dir
    rootdir = bsenv.rootdir

    if 'optional' in bsopts:
        optlist = bsopts['optional']
    else:
        optlist = []

    #For Ubuntu 24.04, the kernel module is compressed with zstd, but the modprobe binary in tizen bootstrap
    #don't support zstd compression. Need to load needed kernel module on host PC firstly.
    for part in sorted(kickstart.get_partitions(cropts['ks']),
                               key=lambda p: p.mountpoint):
        if part.fstype == "btrfs" or part.fstype == "f2fs":
            load_module(part.fstype)

    try:
        msger.info("Creating %s bootstrap ..." % distro)
        bsenv.create(cropts['repomd'], pkglist, optlist)

        # bootstrap is relocated under "bootstrap"
        if os.path.exists(os.path.join(rootdir, "bootstrap")):
            rootdir = os.path.join(rootdir, "bootstrap")

        bsenv.dirsetup(rootdir)
        if cropts['use_mic_in_bootstrap']:
            msger.info("No copy host mic")
        else:
            #when mic in mic-bootstrap is py2, use mic version in mic-bootstrap.
            if (mic_py2_in_mic_bootstrap(os.path.join(rootdir, '/usr/bin/mic'.lstrip('/'))) == True):
                msger.info("Copy host mic conf to bootstrap")
                sync_mic_conf(rootdir)
            else:
                msger.info("Copy host mic to bootstrap")
                sync_mic(rootdir, plugin=cropts['plugin_dir'])

        #FIXME: sync the ks file to bootstrap
        if "/" == os.path.dirname(os.path.abspath(configmgr._ksconf)):
            safecopy(configmgr._ksconf, rootdir)

        msger.info("Start mic in bootstrap: %s\n" % rootdir)
        bsarch = ELF_arch(rootdir)
        if bsarch in personality_defs:
            condPersonality(bsarch)
        bindmounts = get_bindmounts(cropts)
        ret = bsenv.run(argv, cwd, rootdir, bindmounts)

    except errors.BootstrapError as err:
        raise errors.CreatorError("Failed to download/install bootstrap package " \
                                  "or the package is in bad format: %s" % err)
    except RuntimeError as err:
        #change exception type but keep the trace back
        value,tb = sys.exc_info()[1:]
        raise errors.CreatorError((value,tb))
    else:
        if not ret:
            run_scripts_out_bootstrap(cropts['ks'], cropts['outdir'])
        sys.exit(ret)
    finally:
        bsenv.cleanup()

def get_bindmounts(cropts):
    binddirs =  [
                  os.getcwd(),
                  cropts['tmpdir'],
                  cropts['cachedir'],
                  cropts['outdir'],
                  cropts['local_pkgs_path'],
                ]
    bindfiles = [
                  cropts['logfile'],
                  configmgr._ksconf,
                ]

    for lrepo in cropts['localrepos']:
        binddirs.append(lrepo)
    for ltpkrepo in cropts['localtpkrepos']:
        binddirs.append(ltpkrepo)

    bindlist = list(map(expath, [_f for _f in binddirs if _f]))
    bindlist += list(map(os.path.dirname, list(map(expath, [_f for _f in bindfiles if _f]))))
    bindlist = sorted(set(bindlist))
    bindmounts = ';'.join(bindlist)
    return bindmounts


def get_mic_binpath():
    fp = None
    try:
        import pkg_resources # depends on 'setuptools'
        dist = pkg_resources.get_distribution('mic')
        # the real script is under EGG_INFO/scripts
        if dist.has_metadata('scripts/mic'):
            fp = os.path.join(dist.egg_info, "scripts/mic")
    except ImportError:
        pass
    except pkg_resources.DistributionNotFound:
        pass


    if fp:
        return fp

    # not found script if 'flat' egg installed
    try:
        return find_binary_path('mic')
    except errors.CreatorError:
        raise errors.BootstrapError("Can't find mic binary in host OS")


def get_mic_modpath():
    try:
        import mic
    except ImportError:
        raise errors.BootstrapError("Can't find mic module in host OS")
    path = os.path.abspath(mic.__file__)
    return os.path.dirname(path)

def get_mic_libpath():
    return os.getenv("MIC_LIBRARY_PATH", "/usr/lib/mic")

def sync_mic_conf(bootstrap, conf = '/etc/mic/mic.conf'):
    _path = lambda p: os.path.join(bootstrap, p.lstrip('/'))

    try:
        safecopy(conf, _path(conf), False)
    except (OSError, IOError) as err:
        raise errors.BootstrapError(err)

    # auto select backend
    with open(_path(conf), 'r') as rf:
        conf_str = rf.read()
    conf_str = re.sub(r"pkgmgr\s*=\s*.*", "pkgmgr=auto", conf_str)
    with open(_path(conf), 'w') as wf:
        wf.write(conf_str)

# the hard code path is prepared for bootstrap
def sync_mic(bootstrap, binpth = '/usr/bin/mic',
             libpth='/usr/lib',
             plugin='/usr/lib/mic/plugins',
             pylib = '/usr/lib/python3/site-packages',
             conf = '/etc/mic/mic.conf'):
    _path = lambda p: os.path.join(bootstrap, p.lstrip('/'))

    micpaths = {
                 'binpth': get_mic_binpath(),
                 'libpth': get_mic_libpath(),
                 'plugin': plugin,
                 'pylib': get_mic_modpath(),
                 'conf': '/etc/mic/mic.conf',
               }

    if not os.path.exists(_path(pylib)):
        pyptn = '/usr/lib/python3.*/site-packages'
        pylibs = glob.glob(_path(pyptn))
        if pylibs:
            pylib = pylibs[0].replace(bootstrap, '')
        else:
            raise errors.BootstrapError("Can't find python site dir in: %s" %
                                        bootstrap)

    for key, value in list(micpaths.items()):
        try:
            safecopy(value, _path(eval(key)), False, ["*.pyc", "*.pyo"])
        except (OSError, IOError) as err:
            raise errors.BootstrapError(err)

    # auto select backend
    with open(_path(conf), 'r') as rf:
        conf_str = rf.read()
    conf_str = re.sub(r"pkgmgr\s*=\s*.*", "pkgmgr=auto", conf_str)
    with open(_path(conf), 'w') as wf:
        wf.write(conf_str)

    # chmod +x /usr/bin/mic
    os.chmod(_path(binpth), 0o777)

def safecopy(src, dst, symlinks=False, ignore_ptns=()):
    if os.path.isdir(src):
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        if os.path.exists(dst):
            shutil.rmtree(dst, ignore_errors=True)

        src = src.rstrip('/')
        # check common prefix to ignore copying itself
        if dst.startswith(src + '/'):
            ignore_ptns = list(ignore_ptns) + [ os.path.basename(src) ]

        ignores = shutil.ignore_patterns(*ignore_ptns)
        try:
            shutil.copytree(src, dst, symlinks, ignores)
        except (OSError, IOError):
            shutil.rmtree(dst, ignore_errors=True)
            raise
    else:
        if not os.path.isdir(dst):
            makedirs(os.path.dirname(dst))

        shutil.copy2(src, dst)

def prepare_create(args):
    """
    Usage:
        ${name} ${cmd_name} <ksfile> [OPTS]

    ${cmd_option_list}
    """

    if args is None:
        raise errors.Usage("Invalid arguments.")

    creatoropts = configmgr.create
    ksconf = args.ksfile

    if creatoropts['runtime'] == 'bootstrap':
        configmgr._ksconf = ksconf
        bootstrap_mic()

    recording_pkgs = []
    if len(creatoropts['record_pkgs']) > 0:
        recording_pkgs = creatoropts['record_pkgs']

    if creatoropts['release'] is not None:
        if 'name' not in recording_pkgs:
            recording_pkgs.append('name')
        if 'vcs' not in recording_pkgs:
            recording_pkgs.append('vcs')

    configmgr._ksconf = ksconf

    # try to find the pkgmgr
    pkgmgr = None
    backends = pluginmgr.get_plugins('backend')
    if 'auto' == creatoropts['pkgmgr']:
        for key in configmgr.prefer_backends:
            if key in backends:
                pkgmgr = backends[key]
                break
    else:
        for key in list(backends.keys()):
            if key == creatoropts['pkgmgr']:
                pkgmgr = backends[key]
                break

    if not pkgmgr:
        raise errors.CreatorError("Can't find backend: %s, "
                                  "available choices: %s" %
                                  (creatoropts['pkgmgr'],
                                   ','.join(list(backends.keys()))))
    return creatoropts, pkgmgr, recording_pkgs

