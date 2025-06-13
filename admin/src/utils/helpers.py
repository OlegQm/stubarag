import datetime
import streamlit as st

from common.logging.st_logger import st_logger

# Stores attributes given in 'record_keys' from 'record' to 'data' dictionaries 
def load_header_attributes(data, record, data_keys, record_keys):
    for data_key, record_key in zip(data_keys, record_keys):
        try:
            data[data_key].append(record['header'][record_key])
        except Exception as e:
            st_logger.debug(e)
            data[data_key].append(None)


# Stores attributes given in 'record_keys' from 'record' to 'data' dictionaries 
def load_attributes(data, record, data_keys, record_keys):
    for data_key, record_key in zip(data_keys, record_keys):
        try:
            data[data_key].append(record[record_key])
        except Exception as e:
            st_logger.debug(e)
            data[data_key].append(None)


# Returns dict with keys provided as argument paired with empty lists
def build_empty_dict(keys):
    data = {}
    for dict_key in keys:
        data[dict_key] = []
    return data


# Returns standardized file record based on template to be stored in MongoDB
def create_file_record(file):
    now = datetime.datetime.now()
    date_time = now.strftime("%d-%m-%Y_%H-%M-%S")
    try:
        file_data = file.read()
        file_size = file.size
        file_name = file.name
        file_type = file.type
    except Exception as e:
        st_logger.error(e)
        st.toast("Error: cannot read uploaded file")
        
    # Teplate record
    record = {
        "header": {
            "date_time" : date_time, 
            "file_name" : file_name,
            "author" : "admin",
            "size" : file_size,
            "ingested" : False,
            "md5sum" : None,
            "type" : file_type
        },
        "content": file_data
    }
    return record


def get_rec_id(df: object, selected_row_index: int) -> str:
    """
    Get record ID from pandas DataFrame based on selected row index.

    Args:
        df (pandas.DataFrame): DataFrame with records
        selected_row_index (int): Index of selected row in DataFrame

    Returns:
        str: Record ID
    """
    return df.iloc[selected_row_index]['ID']


def get_rec_descriptor(collection: str, df: object, selected_row_index: int) -> str:
    """
    Get record descriptor from pandas DataFrame based on selected row index.
    Descriptor is unique value readable for humans. 

    Args:
        collection (str): Name of collection in MongoDB
        df (pandas.DataFrame): DataFrame with records
        selected_row_index (int): Index of selected row in DataFrame

    Returns:
        str: Record descriptor (filename, description, URL, etc.)
    """
    match collection:
        case 'knowledge':
            return df.iloc[selected_row_index][st.session_state.translator('Name')]
        case 'history':
            return df.iloc[selected_row_index][st.session_state.translator('Description')]
        case 'webscraper':
            return df.iloc[selected_row_index]['URL']
        case _:
            return df.iloc[selected_row_index]['ID']


def get_columns(collection: str) -> list:
    """
    Create list of columns for dataset based on collection type. This columns
    are used to create pandas DataFrame. Names of columns are displayed on FE.

    Args:
        collection (str): Name of collection in MongoDB

    Returns:
        list: List of columns for dataset
    """
    
    if collection == 'knowledge':
        columns = [
            'ID',
            st.session_state.translator('Name'),
            st.session_state.translator('Date'),
            st.session_state.translator('Author'),
            st.session_state.translator('Size'),
            st.session_state.translator('Ingested'),
            'MD5Sum',
            st.session_state.translator('Type')
        ]
    elif collection == 'history':
        columns = [
            'ID', 
            st.session_state.translator('Description'),  
            st.session_state.translator('User'), 
            st.session_state.translator('Feedback'),
            st.session_state.translator('Review'),
            st.session_state.translator('Reviewed by'),
            st.session_state.translator('Ingested'),
            'Discord',
            st.session_state.translator('Date'),
        ]
    elif collection == 'webscraper':
        columns = [
            'ID',
            st.session_state.translator('Web description'),
            'URL',
            st.session_state.translator('Author'),
            st.session_state.translator('Date'),
        ]
    else:
        columns = None

    return columns


def get_record_keys(collection: str) -> list:
    """
    Create list of keys for record based on collection type. This keys 
    are used to extract data from MongoDB record.

    Args:
        collection (str): Name of collection in MongoDB

    Returns:
        list: List of keys for record
    """

    if collection == 'knowledge':
        record_keys = [
            '_id', 
            'file_name', 
            'date_time', 
            'author', 
            'size', 
            'ingested', 
            'md5sum', 
            'type'
        ]
    elif collection == 'history':
        record_keys = [
            '_id', 
            'title', 
            'user_id', 
            'feedback', 
            'review',
            'reviewed_by',
            'ingested', 
            'discord', 
            'date_time'
        ]
    elif collection == 'webscraper':
        record_keys = [
            '_id', 
            'description', 
            'url', 
            'owner', 
            'date'
        ]
    else:
        record_keys = None

    return record_keys