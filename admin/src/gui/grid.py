import streamlit as st

import src.gui.selection_buttons as btn
from src.utils.mongodb_adapter import create_dataset_from_mongodb


def print_dataframe(collection: str, query: dict = None) -> None:
    """
    Function that prints a table with formated MongoDB records based on the collection and query provided.
    If no query is provided, all records from the collection are printed. Initialisation of the dataframe
    and saving it to the session state is done only once.

    Args:   
        collection (str): Name of the collection where the records are stored
        query (dict): Dictionary containing the query to be executed. Default is None

    Returns:
        None
    """
    # If not loaded, load dataset 
    if ('dataset_' + collection) not in st.session_state:
        st.session_state['dataset_' + collection] = create_dataset_from_mongodb(collection, query)
    
    build_table(collection, st.session_state['dataset_' + collection])


def build_table(collection: str, df: object) -> None:
    """
    Creates a table with formated records from the MongoDB collection provided.
    Displays the table with the records and the selection action buttons on FE.

    Args:
        collection (str): Name of the collection where the records are stored
        df (object): pandas DataFrame object containing the records from MongoDB

    Returns:
        None
    """
    # Placeholder for action buttons on selected rows
    selection_actions_placeholder = st.columns([1,1,1,1,1,1])
    with selection_actions_placeholder[0]:
        st.markdown(st.session_state.translator("Selection actions:"))

    grid = st.dataframe(df, column_config={"ID":None}, on_select='rerun',  selection_mode='multi-row')

    build_selection_buttons(collection, selection_actions_placeholder, df, grid.selection['rows'], disabled=is_selection_empty(grid))
    if grid.selection['rows']:
        build_details_buttons(collection, df, grid.selection['rows'])


def build_selection_buttons(collection: str, columns: st.columns, df: object, selected_rows: list, disabled: bool = False) -> None:
    """
    Displays action buttons in 'columns' object (above grid). The buttons are unique for each collection.

    Args:
        collection (str): Name of the collection where the records are stored
        columns (st.columns): Streamlit columns object
        df (object): pandas DataFrame object containing the records from MongoDB
        selected_rows (list): List of selected row indexes
        disabled (bool): Flag for disabling the buttons. Default is False

    Returns:
        None
    """
    with columns[1]:
        st.button(
            label=st.session_state.translator("Delete"),
            key="delete_btn",
            disabled=disabled,
            on_click=btn.delete_btn,
            args=[collection, df, selected_rows],
        )
    if collection != "webscraper":
        with columns[2]:
            st.button(
                label=st.session_state.translator("Unlearn"),
                key="unlearn_btn",
                disabled=disabled,
                on_click=btn.unlearn_btn,
                args=[collection, df, selected_rows],
            )
        with columns[3]:
            st.button(
                label=st.session_state.translator("Learn"),
                key="learn_btn",
                disabled=disabled,
                on_click=btn.learn_btn,
                args=[collection, df, selected_rows],
            )


def build_details_buttons(collection: str, df: object, selected_rows: list) -> None:
    """
    Displays titles of selected rows + 'DETAILS' button (under grid).

    Args:
        collection (str): Name of the collection where the records are stored
        df (object): pandas DataFrame object containing the records from MongoDB
        selected_rows (list): List of selected row indexes

    Returns:
        None
    """
    st.markdown(st.session_state.translator("Selected:"))
    for selected_row_index in selected_rows:
        display_selected(collection, df, selected_row_index)


def display_selected(collection: str, df: object, selected_row_index: int) -> None:
    """
    Displays one row of the selected record in the Details section.
    
    Args:
        collection (str): Name of the collection where the records are stored
        df (object): pandas DataFrame object containing the records from MongoDB
        selected_row_index (int): Index of the selected row in the DataFrame

    Returns:
        None
    """
    columns = st.columns([3,1])
    with columns[0]:
        match collection:
            case "history":
                st.write(df.iloc[selected_row_index][st.session_state.translator('Description')])
            case "knowledge":
                st.write(df.iloc[selected_row_index][st.session_state.translator('Name')])
            case "webscraper":
                st.write(df.iloc[selected_row_index][st.session_state.translator('Web description')])
            case _:
                st.write(df.iloc[selected_row_index][st.session_state.translator('Name')])
    with columns[1]:
        st.button(
            label=st.session_state.translator("Details"),
            key="details_btn_"+str(selected_row_index),
            on_click=on_details_click,
            args=[collection, selected_row_index]
        )


def on_details_click(collection: str, selected_row_index: int) -> None:
    """
    Callback function for the 'Details' button. Sets the flag to display the details page and the index of the row
    for printing the correct data.

    Args:
        collection (str): Name of the collection where the records are stored
        selected_row_index (int): Index of the selected row in the DataFrame

    Returns:
        None
    """
    # Flag to display details page + index of row for printing correct data
    st.session_state['display_details_page_' + collection] = True
    st.session_state['details_row_index_' + collection] = selected_row_index
    

def is_selection_empty(grid: object) -> bool:
    """
    Function that checks if the selection in the grid is empty.
    Used for disabling the selection action buttons.

    Args:
        grid (object): Streamlit dataframe object

    Returns:
        bool: True if the selection is empty, False otherwise
    """
    return not(bool(len(grid.selection['rows'])))
 