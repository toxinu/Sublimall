# -*- coding:utf-8 -*-
import os
import shutil
import sublime
import subprocess
from subprocess import PIPE

from . import blacklist
from . import SETTINGS_USER_FILE
from .logger import logger
from .utils import is_win
from .utils import get_7za_bin
from .utils import generate_temp_filename
from .utils import generate_temp_path


class Archiver:
    """
    Archiver using external executable
    """
    def __init__(self):
        """
        Stores sublime packages paths
        """
        self.directory_list = {
            sublime.packages_path(): '',
            sublime.installed_packages_path(): '.sublime-package'
        }
        self.packages_bak_path = '%s.bak' % sublime.packages_path()
        self.installed_packages_bak_path = '%s.bak' % (
            sublime.installed_packages_path())
        self.settings = sublime.load_settings(SETTINGS_USER_FILE)

    def _safe_rmtree(self, directory):
        """
        Safely removes a directory
        """
        if os.path.exists(directory):
            shutil.rmtree(directory, ignore_errors=True)

    def _safe_copy(self, source, destination):
        if not os.path.exists(destination):
            shutil.copytree(source, destination, symlinks=True)

    def _safe_move(self, source, destination):
        """
        Safely moves the source to the destination
        """
        if os.path.exists(source):
            shutil.move(source, destination)

    # shutil.copytree fails if dst exists
    def _copy_tree(self, src, dst, symlinks=False, ignore=None):
        logger.info("Copy %s to %s" % (src, dst))
        if not os.path.exists(dst):
            os.makedirs(dst)
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                self._copy_tree(s, d, symlinks, ignore)
            else:
                if not os.path.exists(d) or os.stat(src).st_mtime - os.stat(dst).st_mtime > 1:
                    try:
                        shutil.copy2(s, d)
                    except (Error) as why:
                        logger.error('shutil.copy2 - %s' % why)

    def _get_7za_executable(self):
        """
        Returns absolute 7za executable path
        """
        zip_bin = get_7za_bin()
        if zip_bin is None:
            logger.error("Couldn't find 7za binary")
            raise Exception("Couldn't find 7za binary")
        return zip_bin

    def _get_output_dir(self):
        """
        Returns the default output directory
        """
        # Assuming Packages and Installed Packages are in the same directory !
        return os.path.abspath(os.path.join(
            list(self.directory_list)[0], os.path.pardir))

    def _run_executable(self, command, password=None, **kwargs):
        """
        Runs 7z executable with arguments
        """
        assert command in ['a', 'x']

        # Pack archive
        if command == 'a':
            assert 'output_filename' in kwargs
            command_args = [
                self._get_7za_executable(), command, '-tzip', '-mx=9', '-y']
            if self.settings.get('symlinks', False):
                command_args.append('-l')
            if password:
                command_args.append('-p%s' % password)
            if 'excluded_dirs' in kwargs:
                command_args.extend(
                    ['-x!%s*' % excluded_dir
                        for excluded_dir in kwargs['excluded_dirs']])
            command_args.append(kwargs['output_filename'])
            command_args.extend(self.directory_list.keys())
        # Unpack archive
        elif command == 'x':
            assert all(k in kwargs for k in ['input_file', 'output_dir'])
            command_args = [
                self._get_7za_executable(),
                command,
                '-tzip', '-y', '-o%s' % kwargs['output_dir']]
            if password is not None:
                command_args.append('-p%s' % password)
            command_args.append(kwargs['input_file'])

        # Run command
        startupinfo = None
        extra_args = {}
        if is_win():
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            extra_args.update({'close_fds': True})

        # Remove passphrase from log
        log_args = []
        for a in command_args:
            if a.startswith('-p'):
                log_args.append('%s%s' % (a[:2], '*' * len(a[2:])))
            else:
                log_args.append(a)

        logger.info('Command: %s' % log_args)
        process = subprocess.Popen(
            command_args,
            startupinfo=startupinfo,
            stdout=PIPE,
            stderr=PIPE,
            **extra_args)
        output = process.communicate()
        exitcode = process.wait()

        if exitcode > 0:
            msg = 'Error while running p7zip (exit code: %s)' % exitcode
            logger.error(msg)
            logger.error('Command: %s' % log_args)
            logger.error('Output:\n %s' % str(output))
            raise Exception(msg)

        return exitcode

    def _excludes_from_package_control(self):
        """
        Returns a list of files / directories that Package Control handles
        """
        pc_settings = sublime.load_settings('Package Control.sublime-settings')
        installed_packages = pc_settings.get('installed_packages', [])
        return [
            '%s%s' % (
                os.path.join(os.path.split(directory)[1], package_name),
                suffix)
            for package_name in installed_packages if package_name.lower() != 'package control'
            for directory, suffix in self.directory_list.items()
        ]

    def move_packages_to_backup_dirs(self):
        """
        Moves packages directories to backups
        """
        self.remove_backup_dirs()

        logger.info('Move %s to %s' % (
            sublime.installed_packages_path(),
            self.installed_packages_bak_path))
        self._safe_copy(
            sublime.installed_packages_path(),
            self.installed_packages_bak_path)
        logger.info('Move %s to %s' % (
            sublime.packages_path(), self.packages_bak_path))
        self._safe_copy(
            sublime.packages_path(), self.packages_bak_path)

    def remove_backup_dirs(self):
        """
        Removes packages backups directories
        """
        for directory in [
                self.packages_bak_path,
                self.installed_packages_bak_path]:
            logger.info('Remove old backup dir: %s' % directory)
            self._safe_rmtree(directory)

    def pack_packages(
            self,
            password=None,
            backup=False,
            exclude_from_package_control=True,
            **kwargs):
        """
        Compresses Packages and Installed Packages
        """
        excluded_dirs = kwargs.get('excluded_dirs', [])
        packages_root_path = os.path.basename(sublime.packages_path())
        installed_packages_root_path = os.path.basename(
            sublime.installed_packages_path())

        # Append blacklisted Packages to excluded dirs
        for package in blacklist.packages:
            excluded_dirs.append(os.path.join(packages_root_path, package))

        # Append blacklisted Installed Packages to excluded dirs
        for package in blacklist.installed_packages:
            excluded_dirs.append(os.path.join(
                installed_packages_root_path, package))

        # Append custom ignored packages
        for package in blacklist.get_ignored_packages():
            excluded_dirs.append(package)

        # Add Package Control excludes
        if exclude_from_package_control and not backup:
            excluded_dirs.extend(self._excludes_from_package_control())

        logger.info('Excluded dirs: %s' % excluded_dirs)
        kwargs['excluded_dirs'] = excluded_dirs

        # Generate a temporary output filename if necessary
        if 'output_filename' not in kwargs:
            kwargs['output_filename'] = generate_temp_filename()
        self._run_executable('a', password=password, **kwargs)
        return kwargs['output_filename']

    def unpack_packages(self, input_file, output_dir=None, password=None):
        """
        Uncompresses Packages and Installed Packages
        """
        if output_dir is None:
            output_dir = self._get_output_dir()
        temp_dir = generate_temp_path()
        logger.info('Extract in %s directory' % temp_dir)
        self._run_executable(
            'x',
            password=password,
            input_file=input_file,
            output_dir=temp_dir)
        logger.info('Copy from %s to %s' % (temp_dir, output_dir))
        self._copy_tree(temp_dir, output_dir)
        logger.info('Remove %s' % temp_dir)
        self._safe_rmtree(temp_dir)

