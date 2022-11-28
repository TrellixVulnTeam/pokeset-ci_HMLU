"""
Context manager, which takes a URL to a tarball of some repository,
and provides a temporary local directory of that repository.
"""

import logging
import os
import shutil
import tarfile
import uuid
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve

logger = logging.getLogger(__name__)


class TemporaryRepository(TemporaryDirectory):
    def __init__(self, *, tarball_url):
        super().__init__()
        self.tarball_url = tarball_url

    def __enter__(self):
        super().__enter__()
        filepath = os.path.join(self.name, "temp_{}.tar.gz".format(uuid.uuid4()))
        urlretrieve(self.tarball_url, filepath)
        logger.info("retrieved tarball %s to %s", self.tarball_url, filepath)
        with tarfile.open(filepath) as tar:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tar, path=self.name)
        os.remove(filepath)
        # content is in an inner directory, so move everything one layer up
        inner, *_ = os.listdir(self.name)
        inner_path = os.path.join(self.name, inner)
        for item in os.listdir(inner_path):
            shutil.move(os.path.join(inner_path, item), self.name)
        os.rmdir(inner_path)
        logger.info("extracted tarball to %s", self.name)
        return self.name
