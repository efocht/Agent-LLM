import logging
from typing import Dict
from fastapi import FastAPI, HTTPException, Depends
from Interactions import Interactions
from ApiClient import (
    Agent,
    add_agent,
    delete_agent,
    rename_agent,
    get_agents,
    verify_api_key,
)
from Models import (
    AgentNewName,
    AgentPrompt,
    ToggleCommandPayload,
    AgentCommands,
    AgentSettings,
    AgentConfig,
    ResponseMessage,
)

app = FastAPI()


@app.post("/api/agent", tags=["Agent"], dependencies=[Depends(verify_api_key)])
async def addagent(agent: AgentSettings) -> Dict[str, str]:
    return add_agent(agent_name=agent.agent_name, provider_settings=agent.settings)


@app.post("/api/agent/import", tags=["Agent"], dependencies=[Depends(verify_api_key)])
async def import_agent(agent: AgentConfig) -> Dict[str, str]:
    return add_agent(
        agent_name=agent.agent_name,
        provider_settings=agent.settings,
        commands=agent.commands,
    )


@app.patch(
    "/api/agent/{agent_name}", tags=["Agent"], dependencies=[Depends(verify_api_key)]
)
async def renameagent(agent_name: str, new_name: AgentNewName) -> ResponseMessage:
    rename_agent(agent_name=agent_name, new_name=new_name.new_name)
    return ResponseMessage(message="Agent renamed.")


@app.put(
    "/api/agent/{agent_name}", tags=["Agent"], dependencies=[Depends(verify_api_key)]
)
async def update_agent_settings(
    agent_name: str, settings: AgentSettings
) -> ResponseMessage:
    update_config = Agent(agent_name=agent_name).update_agent_config(
        new_config=settings.settings, config_key="settings"
    )
    return ResponseMessage(message=update_config)


@app.put(
    "/api/agent/{agent_name}/commands",
    tags=["Agent"],
    dependencies=[Depends(verify_api_key)],
)
async def update_agent_commands(
    agent_name: str, commands: AgentCommands
) -> ResponseMessage:
    update_config = Agent(agent_name=agent_name).update_agent_config(
        new_config=commands.commands, config_key="commands"
    )
    return ResponseMessage(message=update_config)


@app.delete(
    "/api/agent/{agent_name}", tags=["Agent"], dependencies=[Depends(verify_api_key)]
)
async def deleteagent(agent_name: str) -> ResponseMessage:
    delete_agent(agent_name=agent_name)
    return ResponseMessage(message=f"Agent {agent_name} deleted.")


@app.get("/api/agent", tags=["Agent"])
async def getagents():
    agents = get_agents()
    return {"agents": agents}


@app.get(
    "/api/agent/{agent_name}", tags=["Agent"], dependencies=[Depends(verify_api_key)]
)
async def get_agentconfig(agent_name: str):
    agent_config = Agent(agent_name=agent_name).get_agent_config()
    return {"agent": agent_config}


@app.post(
    "/api/agent/{agent_name}/prompt",
    tags=["Agent"],
    dependencies=[Depends(verify_api_key)],
)
async def prompt_agent(agent_name: str, agent_prompt: AgentPrompt):
    agent = Interactions(agent_name=agent_name)
    response = await agent.run(
        prompt=agent_prompt.prompt_name,
        **agent_prompt.prompt_args,
    )
    return {"response": str(response)}


@app.get(
    "/api/agent/{agent_name}/command",
    tags=["Agent"],
    dependencies=[Depends(verify_api_key)],
)
async def get_commands(agent_name: str):
    agent = Agent(agent_name=agent_name)
    return {"commands": agent.AGENT_CONFIG["commands"]}


@app.patch(
    "/api/agent/{agent_name}/command",
    tags=["Agent"],
    dependencies=[Depends(verify_api_key)],
)
async def toggle_command(
    agent_name: str, payload: ToggleCommandPayload
) -> ResponseMessage:
    agent = Agent(agent_name=agent_name)
    try:
        if payload.command_name == "*":
            for each_command_name in agent.AGENT_CONFIG["commands"]:
                agent.AGENT_CONFIG["commands"][each_command_name] = payload.enable

            agent.update_agent_config(
                new_config=agent.AGENT_CONFIG["commands"], config_key="commands"
            )
            return ResponseMessage(
                message=f"All commands enabled for agent '{agent_name}'."
            )
        else:
            agent.AGENT_CONFIG["commands"][payload.command_name] = payload.enable
            agent.update_agent_config(
                new_config=agent.AGENT_CONFIG["commands"], config_key="commands"
            )
            return ResponseMessage(
                message=f"Command '{payload.command_name}' toggled for agent '{agent_name}'."
            )
    except Exception as e:
        logging.info(e)
        raise HTTPException(
            status_code=500,
            detail=f"Error enabling all commands for agent '{agent_name}': {str(e)}",
        )