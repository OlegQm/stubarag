import pymongo
import pandas as pd

import src.utils.helpers as helpers
from common.logging.st_logger import st_logger
from common.session.db_connection import mongo_db

# Function that delete a record with ObjectID 'rec_id' from MongoDB history collection
def delete_record(rec_id: str, collection: str) -> pymongo.results.DeleteResult:
    """
    Function that delete a record with ObjectID 'rec_id' from MongoDB collection

    Args:
        rec_id (str): ObjectID of the record to be deleted
        collection (str): Name of the collection where the record is stored

    Returns:
        DeleteResult object: Result of the deletion operation
    """

    mongo_db.set_collection(collection)
    filter = {"_id":rec_id}
    return mongo_db.collection.delete_one(filter)


#Function that returns one record from Mongo based on rec_id
def load_record(rec_id: str, collection: str) -> dict:
    """
    Function that returns one record from MongoDB based on rec_id

    Args:
        rec_id (str): ObjectID of the record to be returned
        collection (str): Name of the collection where the record is stored

    Returns:
        dict: Dictionary containing the record data
    """
    
    mongo_db.set_collection(collection)
    try:
        history_data = mongo_db.collection.find_one({"_id":rec_id})
        if history_data is None:
            raise Exception
        return history_data
    except Exception:
        st_logger.error("Requested document does not exist: "+f"{rec_id}")
        return None 
    

#Function that updates value in header element
def update_record_element(rec_id: str, element_key: str, new_value: any, collection: str) -> pymongo.results.UpdateResult:
    """
    Function that updates value in header element of a record in MongoDB collection

    Args:
        rec_id (str): ObjectID of the record to be updated
        element_key (str): Key of the element to be updated
        new_value (any): New value to be set
        collection (str): Name of the collection where the record is stored

    Returns:
        UpdateResult object: Result of the update operation
    """
    
    mongo_db.set_collection(collection)
    key = 'header.' + element_key
    filter = {"_id":rec_id}
    update = {'$set': {key: new_value}}
    return mongo_db.collection.update_one(filter,update)


# Handles event of file upload on Admin FE
def upload_file(file: object, collection: str) -> pymongo.results.InsertOneResult:
    """
    Function that handles event of file upload on Admin FE. It creates a record based on the uploaded file and stores it in MongoDB.

    Args:   
        file (object): File object that was uploaded
        collection (str): Name of the collection where the record should be stored

    Returns:
        InsertOneResult object: Result of the insertion operation
    """
    
    mongo_db.set_collection(collection)
    record = helpers.create_file_record(file)
    # Send record to MongoDB
    try:
        return mongo_db.collection.insert_one(record)
    except ConnectionError as e:
        st_logger.error("Error during file upload to MongoDB: " + str(e))
        return None


def create_conversations_buffer() -> pymongo.cursor:
    """
    Function that creates a buffer of conversations that have not been reviewed yet.

    Args:   
        None

    Returns:
        conversations_buffer (pymongo.cursor): Cursor object containing the conversations from Mongo that have not been reviewed yet

    """

    mongo_db.set_collection('history')
    filter = {"header.review": None}

    try:
        conversations_buffer = mongo_db.collection.find(filter)
    except ConnectionError as e:
        st_logger.error("Error during conversations load from MongoDB: " + str(e))
        conversations_buffer = []

    return conversations_buffer


def create_dataset_from_mongodb(collection: str, query: dict = None) -> pd.DataFrame:
    """
    Function that creates a dataset from MongoDB based on the collection and query provided.

    Args:   
        collection (str): Name of the collection where the records are stored
        query (dict): Dictionary containing the query to be executed

    Returns:
        pd.DataFrame: DataFrame containing the records from MongoDB
    """

    mongo_db.set_collection(collection)
    try:
        records_buffer = mongo_db.collection.find(query)
    except Exception as e:
        st_logger.error(e)
        records_buffer = None

    columns = helpers.get_columns(collection)
    record_keys = helpers.get_record_keys(collection)

    # Dataset to build the DF from
    data = helpers.build_empty_dict(columns)

    # Loop over buffer elements (individual stored files) and store needed parameters based on 'record_keys'
    for record in records_buffer:
        if collection == 'webscraper':
            helpers.load_attributes(data, record, columns, record_keys)
        else:
            data['ID'].append(record['_id'])
            helpers.load_header_attributes(data, record, columns[1:], record_keys[1:])
    
    return pd.DataFrame(data)