# -*- coding:utf-8 -*-
import os
import shutil
import sublime
import subprocess
from .utils import generate_temp_filename


class Archiver(object):
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
        self.installed_packages_bak_path = '%s.bak' % sublime.installed_packages_path()

    def _safe_rmtree(self, directory):
        """
        Safely removes a directory
        """
        if os.path.exists(directory):
            shutil.rmtree(directory)

    def _safe_move(self, source, destination):
        """
        Safely moves the source to the destination
        """
        if os.path.exists(source):
            shutil.move(source, destination)

    def _is_os_nt(self):
        """
        Returns whether current os is Windows or not
        """
        return os.name == 'nt'

    def _get_7za_executable(self):
        """
        Returns absolute 7za executable path
        """
        return shutil.which('7za') or os.path.join(os.path.dirname(os.path.realpath(__file__)), '7z', '7za' if not self._is_os_nt() else '7za.exe')

    def _get_output_dir(self):
        """
        Returns the default output directory
        """
        return os.path.abspath(os.path.join(list(self.directory_list)[0], os.path.pardir))  # Assuming Packages and Installed Packages are in the same directory !

    def _run_executable(self, command, password=None, **kwargs):
        """
        Runs 7z executable with arguments
        """
        assert command in ['a', 'x']

        if command == 'a':  # Pack archive
            assert 'output_filename' in kwargs
            command_args = [self._get_7za_executable(), command, '-tzip', '-y']
            if password is not None:
                command_args.append('-p%s' % password)
            if 'excluded_dirs' in kwargs:
                command_args.extend(['-xr!%s*' % excluded_dir for excluded_dir in kwargs['excluded_dirs']])
            command_args.append(kwargs['output_filename'])
            command_args.extend(self.directory_list.keys())

        elif command == 'x':  # Unpack archive
            assert all(k in kwargs for k in ['input_file', 'output_dir'])
            command_args = [self._get_7za_executable(), command, '-tzip', '-y', '-o%s' % kwargs['output_dir']]
            if password is not None:
                command_args.append('-p%s' % password)
            command_args.append(kwargs['input_file'])

        # Run command
        startupinfo = None
        if self._is_os_nt():
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.Popen(command_args, startupinfo=startupinfo)
        exitcode = process.wait()

        return exitcode

    def _excludes_from_package_control(self):
        """
        Returns a list of files / directories that Package Control handles
        """
        pc_settings = sublime.load_settings('Package Control.sublime-settings')
        installed_packages = pc_settings.get('installed_packages', [])
        return ['%s%s' % (os.path.join(os.path.split(directory)[1], package_name), suffix) for package_name in installed_packages for directory, suffix in self.directory_list.items()]

    def move_packages_to_backup_dirs(self):
        """
        Moves packages directories to backups
        """
        self.remove_backup_dirs()

        # Packages directory requires a little bit of filtering to exlude sublime-sync
        os.makedirs(self.packages_bak_path)

        self_package_directory = os.path.split(os.path.dirname(__file__))[1]
        for directory in next(os.walk(sublime.packages_path()))[1]:
            if directory != self_package_directory:
                self._safe_move(os.path.join(sublime.packages_path(), directory), self.packages_bak_path)

        self._safe_move(sublime.installed_packages_path(), self.installed_packages_bak_path)

    def remove_backup_dirs(self):
        """
        Removes packages backups directories
        """
        for directory in [self.packages_bak_path, self.installed_packages_bak_path]:
            self._safe_rmtree(directory)

    def pack_packages(self, password=None, **kwargs):
        """
        Compresses Packages and Installed Packages
        """
        excluded_dirs = kwargs.get('excluded_dirs', [])

        # Append sublime-sync to excluded dirs
        excluded_dirs.append(os.path.relpath(os.path.dirname(__file__), os.path.join(sublime.packages_path(), os.pardir)))

        # Add Package Control excludes
        excluded_dirs.extend(self._excludes_from_package_control())

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
        self._run_executable('x', password=password, input_file=input_file, output_dir=output_dir)
