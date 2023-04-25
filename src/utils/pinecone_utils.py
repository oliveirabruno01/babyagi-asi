import pinecone, openai
from src import consts


def pinecone_init(agent):
    pinecone.init(api_key=consts.PINECONE_API_KEY, environment=consts.PINECONE_ENVIRONMENT)

    # Create Pinecone index
    table_name = consts.PINECONE_TABLE_NAME
    dimension = 1536
    metric = "cosine"
    pod_type = "p1"
    if table_name not in pinecone.list_indexes():
        pinecone.create_index(
            table_name, dimension=dimension, metric=metric, pod_type=pod_type
        )

    # Connect to the index
    index = pinecone.Index(table_name)
    agent.indexes[table_name] = index


# Function to query records from the Pinecone index
def search_in_index(agent, index_name, query, top_k=1000):
    results = agent.indexes[index_name].query(query, top_k=top_k, include_metadata=True)
    response = [f"{task.metadata['task']}:\n{task.metadata['result']}\n;" for task in results.matches]
    return response


# Get embedding for the text
def get_ada_embedding(text):
    text = text.replace("\n", " ")
    vector = openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]
    return vector


def append_to_index(agent, content, index_name):
    # [(0, (0, 0), {"task": agent.task_list[0]["task_name"], "result": "result"})]
    agent.indexes[index_name].upsert(content)