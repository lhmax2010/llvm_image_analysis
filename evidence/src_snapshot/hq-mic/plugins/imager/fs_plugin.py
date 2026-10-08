#!/usr/bin/python3 -tt
#
# Copyright (c) 2011 Intel, Inc.
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

import subprocess
from mic import chroot, msger, rt_util
from mic.utils import misc, errors, fs_related, runner
from mic.imager import fs
from mic.plugin import pluginmgr

from mic.pluginbase import ImagerPlugin
class FsPlugin(ImagerPlugin):
    name = 'fs'

    @classmethod
    def do_create(self, args):
        """${cmd_name}: create fs image

        """
        creatoropts, pkgmgr, recording_pkgs = rt_util.prepare_create(args)

        creator = fs.FsImageCreator(creatoropts, pkgmgr)
        creator._include_src = args.include_src

        if len(recording_pkgs) > 0:
            creator._recording_pkgs = recording_pkgs

        self.check_image_exists(creator.destdir,
                                creator.pack_to,
                                [creator.name],
                                creatoropts['release'])

        try:
            creator.check_depend_tools()
            creator.mount(None, creatoropts["cachedir"])
            creator.install()
            creator.tpkinstall()
            #Download the source packages ###private options
            if args.include_src:
                installed_pkgs =  creator.get_installed_packages()
                msger.info('Generating the image with source rpms included ...')
                if not misc.SrcpkgsDownload(installed_pkgs, creatoropts["repomd"],
                        creator._instroot, creatoropts["cachedir"]):
                    msger.warning("Source packages can't be downloaded")

            creator.configure(creatoropts["repomd"])
            creator.copy_kernel()
            creator.unmount()
            creator.package(creatoropts["destdir"])
            creator.create_manifest()
            if creatoropts['release'] is not None:
                creator.release_output(args.ksfile, creatoropts['destdir'],
                        creatoropts['release'])
            creator.print_outimage_info()
        except errors.CreatorError:
            raise
        finally:
            creator.cleanup()

        #Run script of --run_script after image created
        if creatoropts['run_script']:
            cmd = creatoropts['run_script']
            try:
                runner.show(cmd)
            except OSError as err:
                msger.warning(str(err))


        msger.info("Finished.")
        return 0

    @classmethod
    def do_chroot(self, target, cmd=[]):#chroot.py parse opts&args
        try:
            if cmd is not None and len(cmd) != 0:
                cmdline = ' '.join(cmd)
            else:
                cmdline = "/bin/bash"
            envcmd = fs_related.find_binary_inchroot("env", target)
            if envcmd:
                cmdline = "%s HOME=/root %s" % (envcmd, cmdline)
            chroot.chroot(target, None, cmdline)
            return 1
        finally:
            chroot.cleanup_after_chroot("dir", None, None, None)
