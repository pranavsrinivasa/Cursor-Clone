from agents import *


class AgenticAISystem:
    """Main agentic AI system for codebase modifications."""
    
    def __init__(self, repo_path: str, index_path: str = None):
        """Initialize the agentic AI system.
        
        Args:
            repo_path: Path to the repository
            index_path: Optional path to load an existing index
        """
        self.repo_path = repo_path
        self.ingestor = CodebaseIngestor(repo_path)
        self.knowledge_builder = KnowledgeBuilder()
        if index_path and os.path.exists(index_path):
            self.index = self.knowledge_builder.load_index(index_path)
        else:
            logger.info("Index not found or not provided. Building new index.")
            nodes = self.ingestor.ingest()
            self.index = self.knowledge_builder.build_index(nodes)
            if index_path:
                self.knowledge_builder.save_index(self.index, index_path)
        self.planning_agent = PlanningAgent(self.index)
        self.change_executor = ChangeExecutor(repo_path, self.index)
        self.test_runner = TestSandboxRunner(repo_path)
    
    def process_requirement(self, requirement: str) -> Dict:
        """Process a code change requirement.
        
        Args:
            requirement: The change requirement
            branch_name: Optional branch name to create
            
        Returns:
            Processing results
        """
        results = {
            "requirement": requirement,
            "plan": None,
            "changes": None,
            "tests": None,
            "test_results": None,
        }
        logger.info(f"Processing requirement: {requirement}")
        plan = self.planning_agent.create_implementation_plan(requirement)
        results["plan"] = plan
        changes = self.change_executor.execute_plan(plan)
        results["changes"] = changes
        tests = self.test_runner.generate_tests(plan)
        results["tests"] = tests
        test_results = self.test_runner.run_tests()
        results["test_results"] = test_results
        if not results["test_results"].get("success", False):
            analysis = self.test_runner.analyze_test_failures(test_results)
            new_reqs = f"Requirements:{requirement}\nError Analysis: {analysis}"
            results['analysis'] = f" Faild with following analysis {analysis} !! DO NOT COMMIT !!"
        
        return results