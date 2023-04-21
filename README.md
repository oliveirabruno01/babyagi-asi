<h1 align="center">
 Babyagi, an Autonomous and Self-Improving agent: BASI
</h1>

# Last changes

The main changes are that now you can easily enable/disable/add the execution_agent tools, you can choose the amount of n-shots the agent will receive in its prompt, if the agent will keep running in continuous mode even with the list of empty tasks, and pinecone and serp are not activated by default.

This repository will soon be updated to be compatible with the latest commits from the original babyagi.


# Objective
This Python script is an example of a LLM-powered autonomous agent. The system uses OpenAI API to create and execute tasks.
The core idea of the project is to provide the assistant with the tools it needs to do any task - if it's smart enough. 
It can arbitrarily execute code and control its own flow and memory, for a sufficiently intelligent agent, either by pre-training, fine-tuning or prompt-optimization, this should be enough (if it is possible at all).

This is just a PoC in constant development.


# How It Works<a name="how-it-works"></a>
The script works by running an infinite loop that does the following steps:

1- Write a function to finish the most relevant task (execution_agent);
 
2- Save execution to memory if successful (and only if the task does not yet exist in memory, in the future I will implement updates in the memories);
 
3- Read the changes and pass them to execution_agent again or quit the program (change_propagation_agent);

# Dynamic one-shot

The execution_agent one-shot example is dynamically chosen according to the context of the current task, so once BASI has done a task correctly, it will be able to do it more easily in the future. One-shots are in ``/memories``. One could inject examples with hotkey shortcuts, utility codes... to get more out of BASI in everyday life. 

For example BASI can access and post a tweet in the account that is open in the browser thanks to a one-shot that teaches it to post on twitter using the tab key.

Currently, I use gpt.3-5 to choose the one-shot from the execution_agent, but maybe in the future I'll use vector search for that.

# BASI tools

Both agents share the same "personality" and the same chore prompt. 
To enable/disable execution_agent tools change the js object at ``tools/config.json``

execution_agent tools:

- openai_call
- memory_agent (to retrieve and/or save information), disabled by default
- execution_agent (it can call itself)
- count_tokens
- process_large_files
- get_serp_query, disabled by default

memory_agent tools:
- openai_call
- get_ada_embedding
- append_to_index
- search_in_index
- create_new_index (hardcoded disabled)

Execution_agent and memory_agent perform actions by running arbitrary Python code;


# How to Use<a name="how-to-use"></a>
To use the script, you will need to follow these steps:

1. Install the required packages: `pip install -r requirements.txt`
2. Copy the .env.example file to .env: `cp .env.example .env`. This is where you will set the following variables.
3. Set your OpenAI key and model in the OPENAI_API_KEY, OPENAPI_API_MODEL variables.
4. Set your OpenA in the OPENAI_API_KEY, OPENAPI_API_MODEL variables.
6. Set the objective of the task management system in the OBJECTIVE variable. Alternatively you can pass it to the script as a quote argument.
```
python babyagi.py ["<objective>"]
```
8. Set the task_list of the system in the TASK_LIST variable.
9. Run the script.

# Examples
```
OBJECTIVE=I need to complete the first task
TASK_LIST=['I must rickroll myself', 'I must close the tab in which I rickrolled myself']
```

```
OBJECTIVE=I need to complete the first task
TASK_LIST=['I must analyze my cognitive archictecture during my chain of thoughts and then in my 'answer:' I will write 10 examples of multi_step_objective-first_task pairs to showcase my capabilities, I must append the result in the ./output2.txt file.']
```

```
OBJECTIVE=Improve my prompts at ./prompts.py file
TASK_LIST=['Plan what to do. I must create a initial end-to-end task list, which the final task will make my objective completed.']
```

## Running in a container
To run the script inside a docker container:

```
docker-compose run basi
```

# Warning<a name="continous-script-warning"></a>
This script is designed to run indefinitely until the task list is empty. So it can be in an endless loop, depending on the objective and first task.
This script consumes a lot more tokens than the original babyagi, so using GPT-4 can quickly get expensive. I haven't tested it yet.

I recommend using this script in a virtual machine and always making a backup if changing something. BabyAGI can run commands and python code on your computer. The results are almost always unexpected.


# Backstory
BabyAGI is a pared-down version of the original [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (Mar 28, 2023, by @yoheynakajima)


BASI is a modified version of BabyAGI created to show how LLMs can perform in the real world.

Made with focus by [@LatentLich](https://twitter.com/LatentLich)
