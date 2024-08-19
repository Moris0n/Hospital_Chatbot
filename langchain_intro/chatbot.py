from langchain_openai import ChatOpenAI
from langchain.prompts import (
    PromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_elasticsearch import ElasticsearchStore
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain.schema.runnable import RunnablePassthrough
from langchain.agents import (
    create_openai_functions_agent,
    AgentExecutor,
)
from langchain.tools.base import StructuredTool
from langchain import hub
from langchain_intro.tools import get_current_wait_time
from operator import itemgetter
from pydantic import BaseModel
import dotenv
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

dotenv.load_dotenv(encoding='utf-8')

# Define the prompt templates for the Reviews tool
review_template_str = """Your job is to use patient
reviews to answer questions about their experience at
a hospital. Use the following context to answer questions.
Be as detailed as possible, but don't make up any information
that's not from the context. If you don't know an answer, say
you don't know.

{context}
"""

review_system_prompt = SystemMessagePromptTemplate(
    prompt=PromptTemplate(
        input_variables=["context"],
        template=review_template_str,
    )
)

review_human_prompt = HumanMessagePromptTemplate(
    prompt=PromptTemplate(
        input_variables=["question"],
        template="{question}",
    )
)

messages = [review_system_prompt, review_human_prompt]

review_prompt_template = ChatPromptTemplate(
    input_variables=["context", "question"],
    messages=messages,
)

chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

output_parser = StrOutputParser()

# Elasticsearch connection details
ELASTICSEARCH_URL = "http://localhost:9200"
INDEX_NAME = "reviews_index"

# Initialize ElasticsearchStore
elastic_vector_search = ElasticsearchStore(
    es_url=ELASTICSEARCH_URL,
    index_name=INDEX_NAME,
    embedding= HuggingFaceEmbeddings(),
)

# Create a retriever for reviews
reviews_retriever = elastic_vector_search.as_retriever(k=3)

review_chain = (
    {
        "context": itemgetter("question") | reviews_retriever,
        "question": itemgetter("question")
    }
    | review_prompt_template
    | chat_model
    | StrOutputParser()
)

# Define the different tools
class WaitTimeInput(BaseModel):
    hospital_name: str

waits_tool = StructuredTool.from_function(
    name="Waits",
    func=get_current_wait_time,
    description="""Use when asked about current wait times
    at a specific hospital. This tool can only get the current
    wait time at a hospital and does not have any information about
    aggregate or historical wait times. This tool returns wait times in
    minutes. Do not pass the word "hospital" as input,
    only the hospital name itself. For instance, if the question is
    "What is the wait time at hospital A?", the input should be "A".
    """,
    args_schema=WaitTimeInput,
)

review_tool = review_chain.as_tool(
    name="Reviews",
    description="""Handles structured inputs for review processing.
    Useful when you need to answer questions about patient reviews or experiences at the hospital.
    Not useful for answering questions about specific visit details such as payer, billing, treatment, diagnosis,
    chief complaint, hospital, or physician information. Pass the entire question as input to the tool.
    For instance, if the question is "What do patients think about the triage system?", the input should be
    "What do patients think about the triage system?".
    """,
)

# Update tools list with the corrected `Waits` tool
chat_tools = [review_tool, waits_tool]

# Set up the agent using the defined tools
hospital_agent_prompt = hub.pull("hwchase17/openai-functions-agent")

agent_chat_model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)

hospital_agent = create_openai_functions_agent(
    llm=agent_chat_model,
    prompt=hospital_agent_prompt,
    tools=chat_tools,
)

# Create the agent executor
hospital_agent_executor = AgentExecutor(
    agent=hospital_agent,
    tools=chat_tools,
    return_intermediate_steps=True,
    verbose=True,
)

