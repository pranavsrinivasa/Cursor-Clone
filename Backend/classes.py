# This is the old version


# from pydantic import BaseModel, Field
# from typing import Dict, Any, List, Optional

# class AgentIO(BaseModel):
#     """Base class for agent inputs and outputs."""
#     pass

# class CodeAnalyzerInput(AgentIO):
#     code: str = Field(..., description="The original code to analyze")
    
# class CodeAnalyzerOutput(AgentIO):
#     analysis: str = Field(..., description="Analysis of the code structure and purpose")
#     language: str = Field(..., description="Detected programming language")
#     original_code: str = Field(..., description="The original code")

# class StrategistInput(AgentIO):
#     original_code: str = Field(..., description="The original code")
#     analysis: str = Field(..., description="Analysis of the code")
#     language: str = Field(..., description="Programming language of the code")
#     user_prompt: str = Field(..., description="User's request for changes")
    
# class StrategistOutput(AgentIO):
#     improvement_suggestions: str = Field(..., description="Suggested improvements to the code")
#     original_code: str = Field(..., description="The original code")
#     language: str = Field(..., description="Programming language of the code")
#     user_prompt: str = Field(..., description="User's request for changes")

# class ImplementationInput(AgentIO):
#     original_code: str = Field(..., description="The original code")
#     improvement_suggestions: str = Field(..., description="Suggested improvements")
#     language: str = Field(..., description="Programming language of the code")
#     user_prompt: str = Field(..., description="User's request for changes")
    
# class ImplementationOutput(AgentIO):
#     improved_code: str = Field(..., description="The improved version of the code")
#     original_code: str = Field(..., description="The original code")
#     language: str = Field(..., description="Programming language of the code")
#     improvement_suggestions: str = Field(..., description="Improvement suggestions that were applied")

# class ExplanationInput(AgentIO):
#     original_code: str = Field(..., description="The original code")
#     improved_code: str = Field(..., description="The improved version of the code")
#     improvement_suggestions: str = Field(..., description="Improvement suggestions that were applied")
#     language: str = Field(..., description="Programming language of the code")
    
# class ExplanationOutput(AgentIO):
#     explanation: str = Field(..., description="Explanation of the changes made")
#     original_code: str = Field(..., description="The original code")
#     improved_code: str = Field(..., description="The improved version of the code")

# class OrchestratorInput(AgentIO):
#     code: str = Field(..., description="Code that needs improvement")
#     prompt: str = Field(..., description="User's request describing what they want to change")
    
# class OrchestratorOutput(AgentIO):
#     original_code: str = Field(..., description="The original code")
#     improved_code: str = Field(..., description="The improved version of the code")
#     explanation: str = Field(..., description="Explanation of the changes made")
#     language: str = Field(..., description="Detected programming language")


# class BaseAgent:
#     """Base class for all agents in the system."""
    
#     def __init__(self, name: str):
#         self.name = name
        
#     def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
#         """Process inputs and return outputs"""
#         raise NotImplementedError("Each agent must implement its own process method")