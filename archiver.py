# -*- coding:utf-8 -*-
import os
import shutil
import sublime
import sublime_plugin
from zipfile import ZipFile
from .settings import logger
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
            shutil.rmtree(directory, ignore_errors=True)

    def _safe_copy(self, source, destination):
        if os.path.exists(source):
            shutil.copytree(source, destination)

    def _safe_move(self, source, destination):
        """
        Safely moves the source to the destination
        """
        if os.path.exists(source):
            shutil.move(source, destination)

    def _get_output_dir(self):
        """
        Returns the default output directory
        """
        # Assuming Packages and Installed Packages are in the same directory !
        return os.path.abspath(os.path.join(list(self.directory_list)[0], os.path.pardir))

    def _run_archiver(self, command, password=None, **kwargs):
        """
        Runs archiver
        """
        assert command in ['a', 'x']

        # Pack archive
        if command == 'a':
            assert 'output_filename' in kwargs
            output_filename = kwargs.get('output_filename')

            # Open archive
            with ZipFile(output_filename, mode='w') as z:
                # Set password
                if password:
                    z.setpassword(bytes(password.encode('utf-8')))

                skip = False
                logger.info('[Archiver] Archive output: %s' % output_filename)
                logger.info('[Archiver] Dirs to exclude: %s' % ','.join(kwargs.get('excluded_dirs', [])))
                # Dirs to include (Installed Packages and Packages)
                for root_dir in self.directory_list.keys():
                    # For each files in Installed Packages and Packages
                    for d in os.listdir(root_dir):
                        absolute_d = os.path.join(root_dir, d)

                        # Create path like that: Packages/Sublimall to compare with excluded dirs
                        n_split = os.path.split(absolute_d)
                        n_split = (os.path.split(n_split[-2])[-1], n_split[-1],)

                        # Now iterate on excluded dirs
                        for exclu in kwargs.get('excluded_dirs'):
                            # Create similare path like that: Packages/Sublimall for exclude
                            f_split = os.path.split(exclu)
                            # Compare Packages 
                            if f_split[-1] == n_split[-1] and f_split[-2] == n_split[-2]:
                                skip = True
                                break
                        arch_path = os.path.join(n_split[-2], n_split[-1])

                        if skip:
                            logger.info('[Archiver] Ignoring %s' % arch_path)
                            skip = False
                            continue

                        if os.path.isdir(absolute_d):
                            for root, dirs, files in os.walk(absolute_d):
                                for f in files:
                                    relDir = os.path.relpath(root, absolute_d)
                                    relFile = os.path.join(relDir, f)
                                    logger.info('[Archiver] Adding %s' % os.path.join(arch_path, relFile))
                                    z.write(os.path.join(root, f), os.path.join(arch_path, relFile))
                        else:
                            logger.info('[Archiver] Adding %s' % arch_path)
                            z.write(absolute_d, arch_path)
            z.close()
            exitcode = 0
        # Unpack archive
        elif command == 'x':
            assert all(k in kwargs for k in ['input_file', 'output_dir'])
            with ZipFile(kwargs.get('input_file'), mode='r') as z:
                z.extractall(kwargs.get('output_dir'), pwd=password)
            z.close()
            exitcode = 0

        return exitcode

    def _excludes_from_package_control(self):
        """
        Returns a list of files / directories that Package Control handles
        """
        pc_settings = sublime.load_settings('Package Control.sublime-settings')
        installed_packages = pc_settings.get('installed_packages', [])
        return [
            '%s%s' % (os.path.join(os.path.split(directory)[1], package_name), suffix)
            for package_name in installed_packages if package_name.lower() != 'package control'
            for directory, suffix in self.directory_list.items()
        ]

    def move_packages_to_backup_dirs(self):
        """
        Moves packages directories to backups
        """
        self.remove_backup_dirs()

        # Packages directory requires a little bit of filtering to exlude sublimall
        os.makedirs(self.packages_bak_path)
        logger.info('Create new package bak dir: %s' % self.packages_bak_path)

        self_package_directory = os.path.split(os.path.dirname(__file__))[1]
        for directory in next(os.walk(sublime.packages_path()))[1]:
            if directory != self_package_directory:
                logger.info('Move %s package to %s' % (
                    os.path.join(sublime.packages_path(), directory),
                    self.packages_bak_path))
                self._safe_move(
                    os.path.join(sublime.packages_path(), directory),
                    self.packages_bak_path)

        logger.info('Move %s to %s' % (
            sublime.installed_packages_path(), self.installed_packages_bak_path))
        self._safe_copy(
            sublime.installed_packages_path(), self.installed_packages_bak_path)

    def remove_backup_dirs(self):
        """
        Removes packages backups directories
        """
        for directory in [self.packages_bak_path, self.installed_packages_bak_path]:
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

        # Append sublimall to excluded dirs
        excluded_dirs.append(
            os.path.relpath(
                os.path.dirname(__file__),
                os.path.join(sublime.packages_path(), os.pardir)))

        # Add Package Control excludes
        if exclude_from_package_control and not backup:
            excluded_dirs.extend(self._excludes_from_package_control())

        kwargs['excluded_dirs'] = excluded_dirs

        # Generate a temporary output filename if necessary
        if 'output_filename' not in kwargs:
            kwargs['output_filename'] = generate_temp_filename()
        self._run_archiver('a', password=password, **kwargs)
        return kwargs['output_filename']

    def unpack_packages(self, input_file, output_dir=None, password=None):
        """
        Uncompresses Packages and Installed Packages
        """
        if output_dir is None:
            output_dir = self._get_output_dir()
        self._run_archiver(
            'x', password=password, input_file=input_file, output_dir=output_dir)
