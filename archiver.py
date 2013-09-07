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
        self.directory_list = [
            sublime.packages_path(),
            sublime.installed_packages_path()
        ]
        self.packages_bak_path = '%s.bak' % sublime.packages_path()
        self.installed_packages_bak_path = '%s.bak' % sublime.installed_packages_path()

    def _safe_rmtree(self, directory):
        """
        Safely removes a directory
        """
        if os.path.exists(directory):
            shutil.rmtree(directory)

    def _is_os_nt(self):
        """
        Returns whether current os is Windows or not
        """
        return os.name == 'nt'

    def _get_7za_executable(self):
        """
        Returns absolute 7za executable path
        """
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), '7z', '7za' if not self._is_os_nt() else '7za.exe')

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
            if 'excluded_dir' in kwargs:
                command_args.append('-xr!%s*' % kwargs['excluded_dir'])
            command_args.append(kwargs['output_filename'])
            command_args.extend(self.directory_list)

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
                shutil.move(os.path.join(sublime.packages_path(), directory), self.packages_bak_path)

        shutil.move(sublime.installed_packages_path(), self.installed_packages_bak_path)

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
            output_dir = os.path.join(self.directory_list[0], os.pardir)
        self._run_executable('x', password=password, input_file=input_file, output_dir=output_dir)
