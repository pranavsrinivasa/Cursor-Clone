# Old Version
# import os
# import re
# import logging
# from classes import *
# from llama_index.core import Settings
# from llama_index.llms.gemini import Gemini
# from llama_index.core.agent import FunctionCallingAgent, FunctionCallingAgent,ReActAgent
# from llama_index.core.tools import FunctionTool
# from llama_index.core.query_engine import RouterQueryEngine
# import google.generativeai as genai


# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# from dotenv import load_dotenv

# load_dotenv()

# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# if not GOOGLE_API_KEY:
#     raise ValueError("GOOGLE_API_KEY environment variable is required")


# llm = Gemini(
#     api_key=GOOGLE_API_KEY,
#     model="models/gemini-2.0-flash",
#     temperature=0.2
# )

# Settings.llm = llm


# class CodeAnalyzerAgent(BaseAgent):
#     """Agent responsible for analyzing and understanding the input code."""
    
#     def __init__(self):
#         super().__init__("Code Analyzer")
        
#         analyze_code_tool = FunctionTool.from_defaults(
#             name="analyze_code",
#             description="Analyzes the structure, purpose, and components of game development code",
#             fn=self._analyze_code
#         )
        
#         detect_language_tool = FunctionTool.from_defaults(
#             name="detect_language",
#             description="Detects the programming language of the given code",
#             fn=self._detect_language
#         )
        
#         self.agent = FunctionCallingAgent.from_tools(
#             [analyze_code_tool, detect_language_tool],
#             llm=llm,
#             system_prompt="""You are a code analyzer specializing in game development code.
#                 Your role is to analyze code and identify its structure, purpose, and key components.
#                 Focus on game development patterns and techniques. Be thorough but concise.""",
#             verbose=True
#         )
    
#     def _analyze_code(self, code: str) -> str:
#         """Analyze the given code and identify structure, purpose and key components."""
#         return self.agent.query(f"Analyze this game development code and explain its structure, purpose, and key components:\n\n{code}")
    
#     def _detect_language(self, code: str) -> str:
#         """Detect the programming language of the given code."""
#         # # Simple heuristic language detection
#         # if "function" in code and ("{" in code or "=>" in code):
#         #     return "javascript"
#         # elif "def " in code and ":" in code:
#         #     return "python"
#         # elif "void" in code or "int " in code or "float " in code or "public class" in code:
#         #     return "csharp" if "using UnityEngine;" in code else "java"
#         # elif "#include" in code:
#         #     return "cpp"
#         # else:
#             # Let the LLM determine the language
#         response = self.agent.query(f"What programming language is this code written in? Just respond with the language name:\n\n{code}")
#         res = str(response)
#         language = res.lower().strip().split('\n')[0]
#         language = re.sub(r'[^\w\s]', '', language).strip()
#         return language
    
#     def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
#         """Process the inputs and return the analysis results."""
#         logger.info(f"{self.name} processing input")
        
#         code = inputs.get("code", "")
#         analysis = str(self._analyze_code(code))
#         language = self._detect_language(code)
        
#         logger.info(f"{self.name} detected language: {language}")
        
#         return {
#             "analysis": analysis,
#             "language": language,
#             "original_code": code
#         }


# class ImprovementStrategistAgent(BaseAgent):
#     """Agent responsible for identifying potential improvements based on game dev best practices."""
    
#     def __init__(self):
#         super().__init__("Improvement Strategist")
        
#         suggest_improvements_tool = FunctionTool.from_defaults(
#             name="suggest_improvements",
#             description="Suggests code improvements based on game development best practices and user request",
#             fn=self._suggest_improvements
#         )
#         self.agent = FunctionCallingAgent.from_tools(
#             [suggest_improvements_tool],
#             llm=llm,
#             system_prompt="""You are a game development expert who specializes in suggesting code improvements.
#                 Focus on performance, readability, and maintainability best practices in game development.
#                 Your suggestions should be specific, actionable, and directly address the user's request.""",
#             verbose=True
#         )
    
#     def _suggest_improvements(self, code: str, language: str, analysis: str, user_prompt: str) -> str:
#         """Suggest improvements to the code based on game development best practices and user request."""
#         context = f"""
#         Code analysis: {analysis}
        
#         Original code (in {language}):
#         {code}
        
#         User request: {user_prompt}
        
#         Suggest specific improvements to address the user's request and improve this game code following {language} best practices.
#         Focus on the most important changes that would benefit this code. Be specific about what should be changed and why.
#         """
#         return str(self.agent.query(context))
    
#     def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
#         """Process the inputs and return improvement suggestions."""
#         logger.info(f"{self.name} processing input")
        
#         code = inputs.get("original_code", "")
#         analysis = inputs.get("analysis", "")
#         language = inputs.get("language", "unknown")
#         user_prompt = inputs.get("user_prompt", "")
        
#         improvement_suggestions = self._suggest_improvements(code, language, analysis, user_prompt)
        
#         logger.info(f"{self.name} generated improvement suggestions")
        
#         return {
#             "improvement_suggestions": improvement_suggestions,
#             "original_code": code,
#             "language": language,
#             "user_prompt": user_prompt
#         }

# class ImplementationAgent(BaseAgent):
#     """Agent responsible for implementing the suggested improvements."""
    
#     def __init__(self):
#         super().__init__("Implementation Agent")
#         implement_improvements_tool = FunctionTool.from_defaults(
#             name="implement_improvements",
#             description="Implements suggested code improvements",
#             fn=self._implement_improvements
#         )
#         extract_code_tool = FunctionTool.from_defaults(
#             name="extract_code",
#             description="Extracts clean code from text that may contain explanations",
#             fn=self._extract_code
#         )
#         self.agent = FunctionCallingAgent.from_tools(
#             [implement_improvements_tool, extract_code_tool],
#             llm=llm,
#             system_prompt="""You are a game development expert who implements code improvements.
#                 You take original code and suggestions, then produce an improved version.
#                 Your output should be clean, well-formatted, and ready to use in a game project.
#                 Include all necessary imports and keep the original functionality intact while implementing improvements.""",
#             verbose=True
#         )
    
#     def _implement_improvements(self, original_code: str, suggestions: str, language: str, user_prompt: str) -> str:
#         """Implement the suggested improvements to the code."""
#         context = f"""
#         Original code ({language}):
#         {original_code}
        
#         Improvement suggestions:
#         {suggestions}
        
#         User request: {user_prompt}
        
#         Implement these improvements and provide the full improved code. 
#         Make sure your implementation follows the user's request and the suggested improvements.
#         Return ONLY the complete improved code without any explanations or markdown formatting.
#         """
#         return self.agent.query(context)
    
#     def _extract_code(self, text: str) -> str:
#         """Extract clean code from text that may contain explanations."""
#         code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)
#         if code_blocks:
#             return code_blocks[0]
#         return text
    
#     def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
#         """Process the inputs and return the implemented improvements."""
#         logger.info(f"{self.name} processing input")
        
#         code = inputs.get("original_code", "")
#         suggestions = inputs.get("improvement_suggestions", "")
#         language = inputs.get("language", "unknown")
#         user_prompt = inputs.get("user_prompt", "")
#         improved_code = str(self._implement_improvements(code, suggestions, language, user_prompt))
#         improved_code = self._extract_code(improved_code)
        
#         logger.info(f"{self.name} generated improved code")
        
#         return {
#             "improved_code": improved_code,
#             "original_code": code,
#             "language": language,
#             "improvement_suggestions": suggestions
#         }
    
# class ExplanationAgent(BaseAgent):
#     """Agent responsible for explaining the changes made to the code."""
    
#     def __init__(self):
#         super().__init__("Explanation Agent")
#         explain_changes_tool = FunctionTool.from_defaults(
#             name="explain_changes",
#             description="Explains the changes made to the code in a clear way",
#             fn=self._explain_changes
#         )
#         self.agent = FunctionCallingAgent.from_tools(
#             [explain_changes_tool],
#             llm=llm,
#             system_prompt="""You are an expert at explaining code changes to game developers.
#                 Create clear, concise explanations of changes made to code, focusing on:
#                 1. What specific changes were made
#                 2. Why these changes improve the code
#                 3. How these changes benefit game development
#                 Your explanations should be educational and help developers understand best practices.""",
#             verbose=True
#         )
    
#     def _explain_changes(self, original_code: str, improved_code: str, language: str) -> str:
#         """Explain the changes made to the code."""
#         context = f"""
#         Original code ({language}):
#         {original_code}
        
#         Improved code ({language}):
#         {improved_code}
        
#         Provide a clear explanation of:
#         1. What specific changes were made to the code
#         2. Why these changes improve the code
#         3. How these changes benefit game development specifically
        
#         Format the explanation in a way that's easy to read and understand.
#         """
#         return self.agent.query(context)
    
#     def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
#         """Process the inputs and return the explanation."""
#         logger.info(f"{self.name} processing input")
        
#         original_code = inputs.get("original_code", "")
#         improved_code = inputs.get("improved_code", "")
#         language = inputs.get("language", "unknown")
#         explanation = str(self._explain_changes(original_code, improved_code, language))
        
#         logger.info(f"{self.name} generated explanation")
        
#         return {
#             "explanation": explanation,
#             "original_code": original_code,
#             "improved_code": improved_code
#         }
    
# class OrchestratorAgent(BaseAgent):
#     """Agent responsible for coordinating between all other agents."""
    
#     def __init__(self):
#         super().__init__("Orchestrator")
#         self.analyzer = CodeAnalyzerAgent()
#         self.strategist = ImprovementStrategistAgent()
#         self.implementer = ImplementationAgent()
#         self.explainer = ExplanationAgent()
        
#         orchestrate_process_tool = FunctionTool.from_defaults(
#             name="orchestrate_process",
#             description="Orchestrates the entire code improvement process",
#             fn=self._orchestrate_process
#         )
  
#         self.agent = ReActAgent.from_tools(
#             [orchestrate_process_tool],
#             llm=llm,
#             system_prompt="""You are the orchestrator for a game code improvement system.
#                 You coordinate the entire process of analyzing, suggesting improvements, implementing,
#                 and explaining changes to game code. Ensure all steps are executed properly and
#                 the final result meets the user's requirements.""",
#             verbose=True,
#             max_iterations=10
#         )
    
#     def _orchestrate_process(self, code: str, prompt: str) -> Dict[str, Any]:
#         """Orchestrate the entire code improvement process."""
#         logger.info("Starting orchestration process")
        
#         analysis_results = self.analyzer.process({"code": code})
#         logger.info("Code analysis complete")
        
#         strategy_inputs = {
#             **analysis_results, 
#             "user_prompt": prompt
#         }
#         strategy_results = self.strategist.process(strategy_inputs)
#         logger.info("Improvement strategies identified")
        
#         implementation_results = self.implementer.process(strategy_results)
#         logger.info("Improvements implemented")
        
#         explanation_inputs = {
#             **implementation_results,
#             "language": analysis_results.get("language", "unknown")
#         }
#         explanation_results = self.explainer.process(explanation_inputs)
#         logger.info("Explanation generated")
#         final_result = {
#             "original_code": code,
#             "improved_code": implementation_results.get("improved_code", ""),
#             "explanation": explanation_results.get("explanation", ""),
#             "language": analysis_results.get("language", "unknown")
#         }
        
#         return final_result
    
#     def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
#         """Process the user input through the entire pipeline."""
#         code = inputs.get("code", "")
#         prompt = inputs.get("prompt", "")
        
#         result = self._orchestrate_process(code, prompt)
        
#         return result