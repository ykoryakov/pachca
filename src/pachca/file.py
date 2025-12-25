import os
from typing import Optional


class File:

    FILE = 'file'
    IMAGE = 'image'

    def __init__(
        self,
        file_path: str,
        file_type: str = FILE,
        name: Optional[str] = None
    ):
        self.path = file_path
        self.file_type = file_type
        self.name = name or os.path.basename(file_path)
        self.size = os.path.getsize(self.path)

        self.meta: Optional[dict] = None
        self.url: Optional[str] = None
        self.key: Optional[str] = None

    def update_meta(self, meta: dict):
        self.url = meta['direct_url']
        del meta['direct_url']
        self.meta = meta

        key = meta['key']
        self.key = key.replace('${filename}', self.name)

    def as_dict(self):
        return {
            'key': self.key,
            'name': self.name,
            'file_type': self.file_type,
            'size': self.size
        }
