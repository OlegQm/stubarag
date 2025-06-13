import pytest
import streamlit as st


"""

A set of unit tests for chat_app llm package test_connection module.

"""

@pytest.mark.skip(reason="connection_LLM.py tests need update")
@pytest.fixture
def create_chain():

    from frontend.src.llm.llm_agents import setup_chain

    chain = setup_chain()

    return chain


@pytest.mark.skip(reason="connection_LLM.py tests need update")
def test_setup_chain(create_chain):
    
    chain = create_chain
    
    from langchain.chains import ConversationChain

    assert isinstance(chain,ConversationChain), "Failed to setup langchain conversation chain"


@pytest.mark.skip(reason="connection_LLM.py tests need update")
def test_send_query(create_chain):

    chain = create_chain

    from frontend.src.llm.llm_agents import send_query

    from src.llm.streaming import StreamHandler

    streamhandler = StreamHandler(st.empty())

    response = send_query("Are you listening ?",chain,streamhandler)

    assert response != "" and response is not None,"Failed to send query to LLM"


@pytest.mark.skip(reason="connection_LLM.py tests need update")
def test_send_query_logger(create_chain):
    
    chain = create_chain

    from frontend.src.llm.llm_agents import send_query_logger

    response = send_query_logger("Are you listening ?",chain)

    assert response != "" and response is not None,"Failed to send query to LLM"


@pytest.mark.skip(reason="connection_LLM.py tests need update")
def test_count_tokens(create_chain,capsys):
    
    chain = create_chain

    from frontend.src.llm.llm_agents import count_tokens

    response = count_tokens("Are you listening ?",chain)

    assert response != "" and response is not None,"Failed to send query to LLM"

    # Capture the output
    captured = capsys.readouterr()

    # Assert the output is as expected
    assert any(char.isdigit() for char in captured.out),"Failed to return count of tokens"


@pytest.mark.skip(reason="connection_LLM.py tests need update")
def test_load_memory():
    
    messages = [{"role": "user", "content": "Hello there !"},
                {"role": "assistant", "content": "I can hear you !"}]

    memory = load_memory(messages)

    from langchain.chains.conversation.memory import ConversationBufferMemory

    assert isinstance(memory,ConversationBufferMemory),"Failed to create a langchain memory from messages"
