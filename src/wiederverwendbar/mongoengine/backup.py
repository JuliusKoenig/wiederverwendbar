import logging
import os
import shutil
from pathlib import Path
from typing import Union

import bson
from pymongo.database import Database

logger = logging.getLogger(__name__)


def dump(db: Database, path: Union[str, Path], overwrite: bool = False) -> None:
    """
    MongoDB Dump
    :param db: MongoDB database
    :param path: Database dump path
    :param overwrite: Overwrite existing files
    :return: None
    """

    # convert path to Path object
    if type(path) is str:
        path = Path(path)

    logger.debug(f"Dumping database to '{path}'")

    if path.exists():
        if not overwrite:
            raise FileExistsError(f"Path '{path}' already exists")
        if path.is_file():
            # remove existing file
            logger.debug(f"Removing existing file '{path}'")
            os.remove(path)
        else:
            # remove existing files
            logger.debug(f"Removing existing files in '{path}'")
            shutil.rmtree(path)

    # ensure path dir exists
    path.with_suffix("").mkdir(parents=True, exist_ok=True)

    for collection_name in db.list_collection_names():
        logger.debug(f"Dumping collection '{collection_name}'")

        # get all documents from collection
        documents_encoded = []
        for document in db[collection_name].find():
            # encode document to bson
            document_encode = bson.BSON.encode(document)
            documents_encoded.append(document_encode)

        logger.debug(f"Dumping {len(documents_encoded)} documents")

        # create bson file
        bson_file = path.with_suffix("") / f'{collection_name}.bson'
        with open(bson_file, 'wb+') as f:
            # write all documents to bson file
            for document_encode in documents_encoded:
                f.write(document_encode)

    if path.suffix == ".zip":
        # zip dump
        logger.debug(f"Zipping dump '{path.with_suffix('')}' as '{path}'")
        shutil.make_archive(str(path.with_suffix("")), path.suffix.replace(".", ""), path.with_suffix(""))
        logger.debug("Zipped dump successfully")

        # remove bson files
        logger.debug(f"Removing bson files in '{path.with_suffix('')}'")
        shutil.rmtree(path.with_suffix(""))

    logger.debug("Database dumped successfully")


def restore(db: Database, path: Union[str, Path], overwrite: bool = False) -> None:
    """
    MongoDB Restore
    :param db: Database connection
    :param path: Database dump path
    :param overwrite: Overwrite existing collections
    :return: None
    """

    # convert path to Path object
    if type(path) is str:
        path = Path(path)

    logger.debug(f"Restoring database from '{path}'")

    # unzip dump
    if path.suffix == ".zip":
        if path.with_suffix("").is_dir():
            logger.debug(f"Removing existing directory '{path.with_suffix('')}'")
            shutil.rmtree(path.with_suffix(""))
        logger.debug(f"Unzipping dump '{path}'")
        shutil.unpack_archive(path, path.with_suffix(""))
        logger.debug("Unzipped dump successfully")

    # check if path is a directory
    if not os.path.isdir(path.with_suffix("")):
        raise FileNotFoundError(f"Path '{path.with_suffix('')}' does not exist")

    for bson_file in os.listdir(path.with_suffix("")):
        bson_file = path.with_suffix("") / bson_file

        # check bson file is a file
        if not os.path.isfile(bson_file):
            continue

        # check bson file is a bson file
        if not bson_file.suffix == ".bson":
            continue

        # get collection name
        collection_name = bson_file.with_suffix("").name

        logger.debug(f"Restoring collection '{collection_name}'")

        with open(bson_file, 'rb+') as f:
            # read bson file
            bson_file_data = f.read()

            # decode bson file
            documents = bson.decode_all(bson_file_data)

        # drop collection if exists
        if collection_name in db.list_collection_names():
            if overwrite:
                logger.debug(f"Dropping collection '{collection_name}'")
                db[collection_name].drop()
            else:
                raise FileExistsError(f"Collection '{collection_name}' already exists")

        # insert documents into collection
        logger.debug(f"Restoring {len(documents)} documents")
        db[collection_name].insert_many(documents)

    # remove bson files
    if path.suffix == ".zip":
        logger.debug(f"Removing bson files in '{path.with_suffix('')}'")
        shutil.rmtree(path.with_suffix(""))

    logger.debug("Database restored successfully")
