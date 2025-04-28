import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple

import google.generativeai as genai
from llama_index.core import VectorStoreIndex
from llama_index.core.node_parser import CodeSplitter
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core.agent import ReActAgent
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.tools import BaseTool, FunctionTool
from llama_index.core import SimpleDirectoryReader
from llama_index.core import Settings
from llama_index.core.base.response.schema import Response
from git import Repo
from dotenv import load_dotenv
import re
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=GEMINI_API_KEY)

llm = Gemini(
    model_name="gemini-2.0-flash",
    api_key=GEMINI_API_KEY,
    temperature=0.2
)

embed_model = GeminiEmbedding(
    model_name="models/embedding-001",
    api_key=GEMINI_API_KEY,
)

Settings.llm = llm
Settings.embed_model = embed_model


def prepare_for_json(s: str) -> str:
    s = re.sub(r'```json\s*|\s*```', '', s)
    s = re.sub(r',\s*(?=[}\]])', '', s)
    def esc_newlines(m):
        inner = m.group(1).replace('\n', r'\n')
        return f'"{inner}"'
    s = re.sub(r'"([^"]*?)"', esc_newlines, s, flags=re.DOTALL)
    return s

class CodebaseIngestor:
    """Component for ingesting and processing codebase files."""
    
    def __init__(self, repo_path: str):
        """Initialize the codebase ingestor.
        
        Args:
            repo_path: Path to the repository to ingest
        """
        self.repo_path = repo_path
        self.reader = SimpleDirectoryReader(input_dir=self.repo_path,recursive=True)
        self.code_splitter = CodeSplitter(
            language="python",
            chunk_lines=100,
            chunk_lines_overlap=20,
            max_chars=4000
        )
    
    def ingest(self, exclude_dirs: List[str] = None) -> List:
        """Ingest all code files from the repository.
        
        Args:
            exclude_dirs: List of directories to exclude
            
        Returns:
            List of document nodes
        """
        logger.info(f"Ingesting codebase from {self.repo_path}")
        exclude_dirs = exclude_dirs or [".git", "__pycache__", ".venv", "venv", "node_modules"]
        exclude_paths = [os.path.join(self.repo_path, excluded) for excluded in exclude_dirs]
        
        def should_include(path):
            for excluded in exclude_paths:
                if path.startswith(excluded):
                    return False
            return True
        
        all_docs = self.reader.load_data(self.repo_path)
        filtered_docs = [doc for doc in all_docs if should_include(doc.metadata.get("file_path", ""))]
        
        logger.info(f"Found {len(filtered_docs)} code files in repository")
        nodes = self.code_splitter.get_nodes_from_documents(filtered_docs)
        logger.info(f"Split into {len(nodes)} code nodes")
        
        return nodes


class KnowledgeBuilder:
    """Component for building a knowledge index from code nodes."""
    
    def __init__(self):
        """Initialize the knowledge builder."""
        pass
    
    def build_index(self, nodes: List) -> VectorStoreIndex:
        """Build a searchable index from code nodes.
        
        Args:
            nodes: List of document nodes
            
        Returns:
            A VectorStoreIndex built from the nodes
        """
        logger.info("Building knowledge index from code nodes")
        index = VectorStoreIndex(
            nodes=nodes
        )
        logger.info("Knowledge index built successfully")
        return index
    
    def save_index(self, index: VectorStoreIndex, path: str):
        """Save the index to disk.
        
        Args:
            index: The index to save
            path: Path to save the index
        """
        logger.info(f"Saving index to {path}")
        index.storage_context.persist(persist_dir=path)
    
    def load_index(self, path: str) -> VectorStoreIndex:
        """Load an index from disk.
        
        Args:
            path: Path to load the index from
            
        Returns:
            The loaded index
        """
        logger.info(f"Loading index from {path}")
        from llama_index import StorageContext, load_index_from_storage
        storage_context = StorageContext.from_defaults(persist_dir=path)
        index = load_index_from_storage(storage_context)
        return index


class PlanningAgent:
    """Agent for planning code changes based on requirements."""
    
    def __init__(self, index: VectorStoreIndex):
        """Initialize the planning agent.
        
        Args:
            index: The knowledge index
        """
        self.index = index
        self.query_engine = index.as_query_engine(
            response_mode="tree_summarize",
            verbose=True
        )
        self.tools = [
            FunctionTool.from_defaults(
                fn=self.search_codebase,
                name="search_codebase",
                description="Search the codebase for information about specific code components or patterns"
            ),
            FunctionTool.from_defaults(
                fn=self.analyze_dependencies,
                name="analyze_dependencies",
                description="Analyze dependencies between components in the codebase"
            ),
            # FunctionTool.from_defaults(
            #     fn=self.generate_plan,
            #     name="generate_plan",
            #     description="Generate a plan for implementing a change"
            # )
        ]
        self.agent = ReActAgent.from_tools(
            self.tools,
            llm=llm,
            verbose=True,
            context="""You are a Planning Agent
            Instrucutions:
            - Generate a plan to develop a code base base on the requirements
            - Search the codebase to find relevant files using search_codebase tool
            - If relevant files exist analyze the dependencies between then usig analyze_dependencies tool
            - With the information generate a plan with the following fields
                Your plan should include:
                1. Files that need to be modified or created
                2. Specific changes needed in each file
                3. Implementation steps in order
                4. Potential risks or considerations
                5. Tests that should be added or modified
            - You plan should always include the mentioned fields.
            - Do not deviate from the instructions""",
            max_iterations=20
        )
    
    def search_codebase(self, query: str) -> str:
        """Search the codebase for specific information.
        
        Args:
            query: The search query
            
        Returns:
            Search results as a string
        """
        logger.info(f"Searching codebase for: {query}")
        response = self.query_engine.query(query)
        return str(response)
    
    def analyze_dependencies(self, component: str) -> str:
        """Analyze dependencies for a component.
        
        Args:
            component: The component to analyze
            
        Returns:
            Dependency analysis as a string
        """
        logger.info(f"Analyzing dependencies for component: {component}")
        query = f"Identify and list all dependencies of {component} in the codebase. Include both imports and functional dependencies."
        response = self.query_engine.query(query)
        return str(response)
    
    def generate_plan(self, requirement: str) -> Dict:
        """Generate a plan for implementing a change.
        
        Args:
            requirement: The change requirement
            
        Returns:
            A plan as a dictionary
        """
        logger.info(f"Generating plan for requirement: {requirement}")
        
        code_structure = self.search_codebase("Summarize the overall structure and architecture of the codebase")
        
        prompt = f"""
        Based on the following requirement and codebase structure, generate a detailed implementation plan:
        
        REQUIREMENT:
        {requirement}
        
        CODEBASE STRUCTURE:
        {code_structure}
        
        Your plan should include:
        1. Files that need to be modified or created
        2. Specific changes needed in each file
        3. Implementation steps in order
        4. Potential risks or considerations
        5. Tests that should be added or modified
        """
        
        response = llm.complete(prompt)
        plan_text = response.text
        return plan_text
    
    def create_implementation_plan(self, requirement: str) -> Dict:
        """Create a comprehensive implementation plan.
        
        Args:
            requirement: The change requirement
            
        Returns:
            An implementation plan
        """
        logger.info(f"Creating implementation plan for: {requirement}")
        
        plan_question = f"Create a detailed implementation plan for this requirement: {requirement}"
        plan_response = self.agent.query(plan_question)
        structure_prompt = f"""
        Convert the following implementation plan into a structured JSON format:
        {plan_response}
        
        The JSON should have these keys:
        - files_to_modify: array of file paths
        - files_to_create: array of file paths
        - implementation_steps: array of step descriptions
        - potential_risks: array of risk descriptions
        - tests: array of test descriptions
        
        Return only valid JSON without any explanation.
        Do not add any additional fields to the JSON format.
        The JSON result should be populated with only the specified fields.
        """
        
        try:
            structured_response = llm.complete(structure_prompt)
            struct_resp = prepare_for_json(structured_response.text)
            logger.info(struct_resp)
            plan = json.loads(struct_resp)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parsing plan to JSON: {e}")
            plan = {
                "raw_plan": plan_response,
                "files_to_modify": [],
                "files_to_create": [],
                "implementation_steps": [],
                "potential_risks": [],
                "tests": []
            }
        
        return plan


class ChangeExecutor:
    """Component for executing code changes based on plans."""
    
    def __init__(self, repo_path: str, index: VectorStoreIndex):
        """Initialize the change executor.
        
        Args:
            repo_path: Path to the repository
            index: The knowledge index
        """
        self.repo_path = repo_path
        self.index = index
        self.query_engine = index.as_query_engine()
    
    def execute_plan(self, plan: Dict) -> Dict:
        """Execute a change plan.
        
        Args:
            plan: The implementation plan
            
        Returns:
            Execution results
        """
        logger.info("Executing implementation plan")
        results = {
            "modified_files": [],
            "created_files": [],
            "errors": []
        }
        for file_path in plan.get("files_to_modify", []):
            try:
                full_path = os.path.join(self.repo_path, file_path)
                if not os.path.exists(full_path):
                    results["errors"].append(f"File not found: {file_path}")
                    continue
                
                with open(full_path, 'r') as f:
                    original_content = f.read()
                new_content = self.mod_file_gen(file_path, original_content, plan)
                with open(full_path, 'w') as f:
                    f.write(new_content)
                
                results["modified_files"].append(file_path)
                logger.info(f"Modified file: {file_path}")
                
            except Exception as e:
                error_msg = f"Error modifying {file_path}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        for file_path in plan.get("files_to_create", []):
            try:
                full_path = os.path.join(self.repo_path, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                new_content = self.new_file_gen(file_path, plan)
                with open(full_path, 'w') as f:
                    f.write(new_content)
                
                results["created_files"].append(file_path)
                logger.info(f"Created file: {file_path}")
                
            except Exception as e:
                error_msg = f"Error creating {file_path}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        return results
    
    def mod_file_gen(self, file_path: str, original_content: str, plan: Dict) -> str:
        """Generate changes for an existing file.
        
        Args:
            file_path: Path to the file
            original_content: Original file content
            plan: The implementation plan
            
        Returns:
            New file content
        """
        file_specific_steps = []
        for step in plan.get("implementation_steps", []):
            if file_path in step:
                file_specific_steps.append(step)
        file_context = self.search_codebase_for_file(file_path)
        prompt = f"""
        I need to modify the following file according to these implementation steps:
        
        FILE PATH: {file_path}
        
        ORIGINAL CONTENT:
        ```
        {original_content}
        ```
        
        RELEVANT IMPLEMENTATION STEPS:
        {file_specific_steps}
        
        ADDITIONAL CONTEXT FROM CODEBASE:
        {file_context}
        
        Please generate the complete new content for this file with all necessary changes implemented.
        Return only the file content without any explanations or markdown formatting.
        """
        
        response = llm.complete(prompt)
        new_content = response.text
        new_content = new_content.replace("```python", "").replace("```", "").strip()
        
        return new_content
    
    def new_file_gen(self, file_path: str, plan: Dict) -> str:
        """Generate content for a new file.
        
        Args:
            file_path: Path to the file
            plan: The implementation plan
            
        Returns:
            New file content
        """
        file_specific_steps = []
        for step in plan.get("implementation_steps", []):
            if file_path in step:
                file_specific_steps.append(step)
        
        file_ext = os.path.splitext(file_path)[1]
        similar_files_context = self.search_codebase_for_similar_files(file_ext)
        
        prompt = f"""
        I need to create a new file according to these implementation steps:
        
        FILE PATH: {file_path}
        
        RELEVANT IMPLEMENTATION STEPS:
        {file_specific_steps}
        
        SIMILAR FILES CONTEXT:
        {similar_files_context}
        
        Please generate the complete content for this new file.
        Return only the file content without any explanations or markdown formatting.
        """
        
        response = llm.complete(prompt)
        new_content = response.text
        new_content = new_content.replace("```python", "").replace("```", "").strip()
        
        return new_content
    
    def search_codebase_for_file(self, file_path: str) -> str:
        """Search the codebase for information about a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Context information
        """
        query = f"Provide context and information about the file {file_path}, including its purpose and how it's used in the codebase."
        response = self.query_engine.query(query)
        return str(response)
    
    def search_codebase_for_similar_files(self, file_extension: str) -> str:
        """Search the codebase for similar files with the same extension.
        
        Args:
            file_extension: File extension to search for
            
        Returns:
            Context information about similar files
        """
        query = f"Find examples of files with {file_extension} extension in the codebase and summarize their structure and patterns."
        response = self.query_engine.query(query)
        return str(response)


class TestSandboxRunner:
    """Component for testing code changes in a sandbox environment."""
    
    def __init__(self, repo_path: str, test_command: str = "pytest"):
        """Initialize the test sandbox runner.
        
        Args:
            repo_path: Path to the repository
            test_command: Command to run tests
        """
        self.repo_path = repo_path
        self.test_command = test_command
    
    def run_tests(self) -> Dict:
        """Run tests on the modified codebase.
        
        Returns:
            Test results
        """
        import subprocess
        import tempfile
        import shutil
        
        logger.info("Running tests in sandbox environment")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox_repo_path = os.path.join(temp_dir, "sandbox_repo")
            shutil.copytree(self.repo_path, sandbox_repo_path)
            os.chdir(sandbox_repo_path)
            try:
                process = subprocess.run(
                    self.test_command,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                success = process.returncode == 0
                output = process.stdout
                error = process.stderr
            except Exception as e:
                success = False
                output = ""
                error = str(e)
            
            os.chdir(self.repo_path)
        
        results = {
            "success": success,
            "output": output,
            "error": error
        }
        
        if success:
            logger.info("Tests passed successfully")
        else:
            logger.error(f"Tests failed: {error}")
        
        return results
    
    def generate_tests(self, plan: Dict) -> Dict:
        """Generate tests for the implemented changes.
        
        Args:
            plan: The implementation plan
            
        Returns:
            Generated test files
        """
        logger.info("Generating tests for implemented changes")
        results = {
            "generated_tests": []
        }
        for file_path in plan.get("files_to_modify", []) + plan.get("files_to_create", []):
            if not file_path.endswith(".py"):
                continue
            if "test_" in os.path.basename(file_path):
                continue
            
            try:
                module_name = os.path.splitext(os.path.basename(file_path))[0]
                test_file_name = f"test_{module_name}.py"
                
                file_dir = os.path.dirname(file_path)
                if "tests" in os.listdir(self.repo_path):
                    test_dir = os.path.join(self.repo_path)
                    if file_dir != "":
                        test_dir = os.path.join(test_dir, os.path.basename(file_dir))
                        os.makedirs(test_dir, exist_ok=True)
                else:
                    test_dir = os.path.join(self.repo_path, file_dir)
                
                test_file_path = os.path.join(test_dir, test_file_name)
                
                with open(os.path.join(self.repo_path, file_path), 'r') as f:
                    original_content = f.read()
                
                test_content = self._generate_test_content(file_path, original_content)
                
                with open(test_file_path, 'w') as f:
                    f.write(test_content)
                
                results["generated_tests"].append(test_file_path)
                logger.info(f"Generated test file: {test_file_path}")
                
            except Exception as e:
                logger.error(f"Error generating test for {file_path}: {str(e)}")
        
        return results
    
    def _generate_test_content(self, file_path: str, file_content: str) -> str:
        """Generate test content for a file.
        
        Args:
            file_path: Path to the file
            file_content: Content of the file
            
        Returns:
            Test content
        """
        prompt = f"""
        Generate pytest test code for the following Python file:
        
        FILE PATH: {file_path}
        
        FILE CONTENT:
        ```python
        {file_content}
        ```
        
        Please create comprehensive tests that cover the functionality in this file.
        Include appropriate imports, test functions, assertions, and any necessary mocks.
        Return only the Python test code without any explanations or markdown formatting.
        """
        
        response = llm.complete(prompt)
        test_content = response.text
        
        logger.info(test_content)
        test_content = test_content.replace("```python", "").replace("```", "").strip()
        return test_content

    def analyze_test_failures(self, test_results: Dict) -> Dict:
        """Analyze test failures and suggest fixes.
        
        Args:
            test_results: Results from running tests
            
        Returns:
            Analysis and suggestions
        """
        if test_results.get("success", False):
            return {"analysis": "All tests passed successfully", "suggestions": []}
        
        logger.info("Analyzing test failures")
        
        error_output = test_results.get("error", "") + test_results.get("output", "")
        
        prompt = f"""
        Analyze the following test failure output and suggest specific fixes:
        
        TEST OUTPUT:
        {error_output}
        
        Please provide:
        1. A summary of what's failing
        2. The likely root causes
        3. Specific suggestions to fix each issue
        
        Format your response as JSON with keys:
        - 'summary': a brief summary of the failures
        - 'root_causes': an array of potential root causes
        - 'fixes': an array of specific suggestions, each with 'file', 'issue', and 'fix' keys
        
        Return only valid JSON without any explanation.
        Response should be directly parsable by json function
        Do not add any additional data that might lead to failed json parsing error
        """
        
        try:
            response = llm.complete(prompt)
            pre_resp = prepare_for_json(response.text)
            analysis = json.loads(pre_resp)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parsing analysis to JSON: {e}")
            analysis = {
                "summary": "Failed to parse test failures",
                "root_causes": ["Unknown"],
                "fixes": [{
                    "file": "unknown",
                    "issue": "Error parsing test output",
                    "fix": "Manual review needed"
                }]
            }
        
        logger.info(f"Analysis complete: {analysis['summary']}")
        return analysis


class VCSIntegrator:
    """Component for integrating changes with version control systems."""
    
    def __init__(self, repo_path: str):
        """Initialize the VCS integrator.
        
        Args:
            repo_path: Path to the repository
        """
        self.repo_path = repo_path
        try:
            self.repo = Repo(repo_path)
            logger.info(f"Successfully initialized git repository at {repo_path}")
        except Exception as e:
            logger.error(f"Failed to initialize git repository: {str(e)}")
            self.repo = None
    
    def commit_changes(self, message: str) -> bool:
        """Commit changes to the repository.
        
        Args:
            message: Commit message
            
        Returns:
            Success flag
        """
        if not self.repo:
            logger.error("No git repository initialized")
            return False
        
        try:
            self.create_branch('cursor_branch')
            self.repo.git.add(".")
            self.repo.git.commit("-m", message)
            logger.info(f"Successfully committed changes: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to commit changes: {str(e)}")
            return False
    
    def create_branch(self, branch_name: str) -> bool:
        """Create a new branch.
        
        Args:
            branch_name: Name of the branch
            
        Returns:
            Success flag
        """
        if not self.repo:
            logger.error("No git repository initialized")
            return False
        
        try:
            self.repo.git.checkout("-b", branch_name)
            logger.info(f"Successfully created and checked out branch: {branch_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create branch: {str(e)}")
            return False
    
    def generate_commit_message(self, plan: Dict, results: Dict) -> str:
        """Generate a commit message for the changes.
        
        Args:
            plan: The implementation plan
            results: Execution results
            
        Returns:
            Commit message
        """
        prompt = f"""
        Generate a clear and descriptive git commit message for the following code changes:
        
        MODIFIED FILES:
        {results.get('modified_files', [])}
        
        CREATED FILES:
        {results.get('created_files', [])}
        
        IMPLEMENTATION STEPS:
        {plan.get('implementation_steps', [])}
        
        Follow these guidelines:
        1. Start with a brief summary line (max 50 chars)
        2. Add a blank line after the summary
        3. Include bullet points with key changes
        4. Keep the message concise but informative
        
        Return only the commit message without any explanation.
        """
        
        response = llm.complete(prompt)
        return response.text.strip()
