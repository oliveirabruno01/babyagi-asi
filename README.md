<h1 align="center">
 Babyagi, an Autonomous and Self-Improving agent: BASI
</h1>

# Objective
This Python script is an example of a LLM-powered autonomous agent. The system uses OpenAI API to create and execute tasks. 


# How It Works<a name="how-it-works"></a>
The script works by running an infinite loop that does the following steps:

1-Write a function to finish the most relevant task (execution_agent);
2-Read the changes and pass them to execution_agent again;

# BASI tools

Both agents share the same "personality" and the same chore prompt. Currently, I have removed the use of Pinecone but will be bringing it back into an agent to handle I/O on different babyagi memory types.

# How to Use<a name="how-to-use"></a>
To use the script, you will need to follow these steps:

1. Install the required packages: `pip install -r requirements.txt`
2. Copy the .env.example file to .env: `cp .env.example .env`. This is where you will set the following variables.
3. Set your OpenAI key and model in the OPENAI_API_KEY, OPENAPI_API_MODEL variables.
6. Set the objective of the task management system in the OBJECTIVE variable. Alternatively you can pass it to the script as a quote argument.
```
./babyagi.py ["<objective>"]
```
7. Set the first task of the system in the FIRST_TASK variable.
8. Run the script.

# Examples
``OBJECTIVE=I need to complete the first task
FIRST_TASK=I must rickroll myself``

``OBJECTIVE=I need to complete the first task
FIRST_TASK=I must analyze my cognitive archictecture during my chain of thoughts and then in my 'answer:' I will write 10 examples of multi_step_objective-first_task pairs to showcase my capabilities, I must append the result in the ./output2.txt file.``

``OBJECTIVE=Improve my prompts at ./prompts.py file
FIRST_TASK=Plan what to do. I must create a initial end-to-end task list, which the final task will make our objective completed.``


# Warning<a name="continous-script-warning"></a>
This script is designed to run indefinitely until the task list is empty. So it can be in an endless loop, depending on the objective and first task.

I recommend using this script in a virtual machine and always making a backup if changing something. BabyAGI can run commands and python code on your computer. The results are almost always unexpected.


# Backstory
BabyAGI is a pared-down version of the original [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (Mar 28, 2023, by @yoheynakajima)


BASI is a modified version of BabyAGI created to show how LLMs can perform in the real world.

Made with focus by [@LatentLich](https://twitter.com/LatentLich)
