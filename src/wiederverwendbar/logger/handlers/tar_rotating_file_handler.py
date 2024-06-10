import os
import tarfile
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Union, Optional


class TarRotatingFileHandler(RotatingFileHandler):
    """
    RotatingFileHandler that archives old log files as tar.gz files
    """

    def __init__(self,
                 name: str,
                 filename: Union[str, Path],
                 mode: str = "a",
                 max_bytes: int = 0,
                 backup_count: int = 0,
                 encoding: Optional[str] = None,
                 delay: bool = False,
                 archive_backup_count: int = 0):
        super().__init__(filename, mode, max_bytes, backup_count, encoding, delay)
        self.set_name(name)
        self.archiveBackupCount = archive_backup_count
        self.archiveBaseFilename = self.baseFilename[:self.baseFilename.rfind('.')]

    def doRollover(self):
        # rotate and delete old log files
        super().doRollover()

        # archive old log files if backupCount limit is reached
        if self.backupCount > 0:
            backup_log_pattern = self.baseFilename + '.%d'
            # get all existing backup logs
            backup_logs = [Path(backup_log_pattern % i) for i in range(1, self.backupCount + 1)]
            backup_logs = [log for log in backup_logs if log.exists()]

            # check if backup count limit is reached
            if len(backup_logs) >= self.backupCount:
                archive_filename_pattern = self.archiveBaseFilename + '_logs.%d.tar.gz'
                archive_count = 0
                # add all backup logs to tar archive
                archive_filename = archive_filename_pattern % archive_count
                while Path(archive_filename).exists():
                    archive_count += 1
                    archive_filename = archive_filename_pattern % archive_count

                    # if archive count limit is reached, delete oldest archive
                    if archive_count > self.archiveBackupCount:
                        archive_count = 0
                        archive_filename = archive_filename_pattern % archive_count
                        os.remove(archive_filename)
                        break

                with tarfile.open(archive_filename, 'w:gz') as tar:
                    for log in backup_logs:
                        tar.add(log, arcname=log.name)
                        os.remove(log)
