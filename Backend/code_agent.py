import os
import json
import logging
import difflib
from typing import Dict, List, Optional, Any, Tuple
import re

logger = logging.getLogger(__name__)

class CodeChangeAgent:
    """Agent responsible for generating precise code changes rather than complete file rewrites."""
    
    def __init__(self, repo_path: str, query_engine: Any):
        """Initialize the code change agent.
        
        Args:
            repo_path: Path to the repository
            query_engine: Query engine for searching the codebase
        """
        self.repo_path = repo_path
        self.query_engine = query_engine
    
    def analyze_file_structure(self, file_path: str) -> Dict:
        """Analyze the structure of a file to understand its components.
        
        Args:
            file_path: Path to the file
            
        Returns:
            A dictionary containing the file structure analysis
        """
        full_path = os.path.join(self.repo_path, file_path)
        if not os.path.exists(full_path):
            return {"error": f"File not found: {file_path}"}
            
        with open(full_path, 'r') as f:
            content = f.read()
            
        query = f"""
        Analyze the structure of this file {file_path} and identify:
        1. Major sections or blocks of code
        2. Class and function definitions
        3. Import statements
        4. Key variables and constants
        
        Format the analysis to identify the line numbers and positions of key elements.
        """
        
        response = self.query_engine.query(query)
        
        # Identify import section lines
        import_lines = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if re.match(r'^import\s+|^from\s+\w+\s+import', line):
                import_lines.append(i)
                
        # Identify class definitions
        class_defs = []
        class_pattern = re.compile(r'^class\s+(\w+)')
        for i, line in enumerate(lines):
            match = class_pattern.match(line)
            if match:
                class_defs.append((i, match.group(1)))
                
        # Identify function definitions
        func_defs = []
        func_pattern = re.compile(r'^def\s+(\w+)')
        for i, line in enumerate(lines):
            match = func_pattern.match(line)
            if match:
                func_defs.append((i, match.group(1)))
        
        return {
            "file_path": file_path,
            "content": content,
            "lines_count": len(lines),
            "import_lines": import_lines,
            "class_definitions": class_defs,
            "function_definitions": func_defs,
            "analysis": str(response)
        }
    
    def identify_change_points(self, file_analysis: Dict, change_description: str) -> List[Dict]:
        """Identify specific points in the file where changes should be made.
        
        Args:
            file_analysis: Analysis of the file structure
            change_description: Description of the changes to make
            
        Returns:
            A list of change points with locations and change types
        """
        query = f"""
        Based on this file analysis and the required changes, identify the exact locations
        where changes should be made. For each change point, specify:
        1. The line number or range to modify
        2. The type of change (add, modify, delete)
        3. A specific description of what needs to be added or modified
        
        File analysis: {file_analysis['analysis']}
        
        Change requirement: {change_description}
        
        Return the information in a concise format focusing on precise locations.
        """
        
        response = self.query_engine.query(query)
        
        # Parse the response for change points
        change_points = self._parse_change_points(str(response), file_analysis)
        return change_points
    
    def _parse_change_points(self, response_text: str, file_analysis: Dict) -> List[Dict]:
        """Parse the response to extract structured change points.
        
        This is a simplified version - in production you might want to 
        use a more sophisticated approach or have the LLM return structured data.
        """
        change_points = []
        
        # Extract line numbers mentioned in the response
        line_numbers = re.findall(r'line(?:s)?\s+(\d+)(?:\s*-\s*(\d+))?', response_text, re.IGNORECASE)
        
        content_lines = file_analysis["content"].split('\n')
        
        for match in line_numbers:
            start_line = int(match[0])
            end_line = int(match[1]) if match[1] else start_line
            
            # Determine change type based on context (simplified)
            change_type = "modify"  # Default
            if "add" in response_text.lower() or "insert" in response_text.lower():
                change_type = "add"
            elif "remove" in response_text.lower() or "delete" in response_text.lower():
                change_type = "delete"
            
            # Get the context around these lines
            context_start = max(0, start_line - 3)
            context_end = min(len(content_lines), end_line + 3)
            context = '\n'.join(content_lines[context_start:context_end])
            
            change_points.append({
                "start_line": start_line,
                "end_line": end_line,
                "type": change_type,
                "context": context
            })
        
        # If no line numbers found, look for function or class names
        if not change_points:
            for class_line, class_name in file_analysis.get("class_definitions", []):
                if class_name.lower() in response_text.lower():
                    change_points.append({
                        "start_line": class_line,
                        "end_line": class_line,
                        "type": "modify_class",
                        "class_name": class_name,
                        "context": content_lines[class_line]
                    })
            
            for func_line, func_name in file_analysis.get("function_definitions", []):
                if func_name.lower() in response_text.lower():
                    change_points.append({
                        "start_line": func_line,
                        "end_line": func_line,
                        "type": "modify_function",
                        "function_name": func_name,
                        "context": content_lines[func_line]
                    })
        
        # If still no change points, add a generic one for imports section
        if not change_points and file_analysis.get("import_lines"):
            last_import = max(file_analysis["import_lines"])
            change_points.append({
                "start_line": last_import + 1,
                "end_line": last_import + 1,
                "type": "add_after_imports",
                "context": "After imports section"
            })
        
        return change_points
    
    def generate_changes(self, file_path: str, change_points: List[Dict], change_description: str) -> Dict:
        """Generate specific code changes for the identified change points.
        
        Args:
            file_path: Path to the file
            change_points: List of identified change points
            change_description: Description of the changes to make
            
        Returns:
            A dictionary containing the original and modified content
        """
        full_path = os.path.join(self.repo_path, file_path)
        with open(full_path, 'r') as f:
            original_content = f.read()
        
        lines = original_content.split('\n')
        modified_lines = lines.copy()
        
        for point in change_points:
            change_type = point["type"]
            start_line = point["start_line"]
            end_line = point["end_line"]
            
            # Get appropriate context for this change point
            context = '\n'.join(lines[max(0, start_line-5):min(len(lines), end_line+5)])
            the_file = '\n'.join(lines[start_line:end_line+1])
            prompt = f"""
            Generate the exact code to {change_type} for this change point in file {file_path}.
            
            Change requirement: {change_description}
            
            Context around the change point:
            {context}
            
            Current code at change point (lines {start_line} to {end_line}):
            {the_file}


            Only return the new code snippet that should replace or be inserted at this location.
            Follow the instructions stricly.
            No explanations or markdown formatting, just the exact code to use."""
            the_file = '\n'.join([lines[i] for i in range(start_line-3, start_line+1)])
            if change_type == "add_after_imports":
                prompt = f"""
                Generate new code to add after the imports section in file {file_path}.
                
                Change requirement: {change_description}
                
                Current imports:
                ```
                {the_file}
                ```
                
                Only return the new code to insert, no explanations or formatting.
                Do not create the whole file again
                """
            
            response = self.query_engine.query(prompt)
            new_code = str(response).strip()
            
            # Remove any markdown code blocks
            new_code = re.sub(r'```[\w]*\n|```', '', new_code)
            print(f'The New Generated Code is:{new_code}')
            # Apply the change based on type
            if change_type == "add" or change_type == "add_after_imports":
                modified_lines = modified_lines[:start_line+1] + new_code.split('\n') + modified_lines[start_line+1:]
            elif change_type == "delete":
                modified_lines = modified_lines[:start_line] + modified_lines[end_line+1:]
            else:  # modify and other types
                modified_lines = modified_lines[:start_line] + new_code.split('\n') + modified_lines[end_line+1:]
        
        modified_content = '\n'.join(modified_lines)
        
        # Generate diff
        diff = list(difflib.unified_diff(
            original_content.splitlines(),
            modified_content.splitlines(),
            fromfile=f'a/{file_path}',
            tofile=f'b/{file_path}',
            lineterm=''
        ))
        
        return {
            "file_path": file_path,
            "original_content": original_content,
            "modified_content": modified_content,
            "diff": '\n'.join(diff),
            "change_points": change_points
        }
    
    def create_new_file(self, file_path: str, change_description: str, similar_files: List[str] = None) -> Dict:
        """Generate content for a new file.
        
        Args:
            file_path: Path to the new file
            change_description: Description of what the file should contain
            similar_files: List of similar files to use as references
            
        Returns:
            A dictionary containing the generated content
        """
        similar_file_contents = []
        
        if similar_files:
            for sim_file in similar_files[:2]:  # Limit to 2 files for context
                full_path = os.path.join(self.repo_path, sim_file)
                if os.path.exists(full_path):
                    with open(full_path, 'r') as f:
                        similar_file_contents.append((sim_file, f.read()))
        
        similar_files_context = ""
        for sim_file, content in similar_file_contents:
            similar_files_context += f"\nSimilar file: {sim_file}\n```\n{content[:1000]}...\n```\n"
        
        prompt = f"""
        Create a new file at {file_path} based on this requirement:
        
        {change_description}
        
        {similar_files_context}
        
        Return only the complete file content without any explanations or markdown formatting.
        """
        
        response = self.query_engine.query(prompt)
        new_content = str(response)
        
        # Remove any markdown code blocks
        new_content = re.sub(r'```[\w]*\n|```', '', new_content).strip()
        
        return {
            "file_path": file_path,
            "content": new_content
        }
    
    def find_similar_files(self, file_path: str) -> List[str]:
        """Find files similar to the given file path.
        
        Args:
            file_path: Path to find similar files for
            
        Returns:
            List of similar file paths
        """
        extension = os.path.splitext(file_path)[1]
        similar_files = []
        
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith(extension) and file != os.path.basename(file_path):
                    rel_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                    similar_files.append(rel_path)
                    if len(similar_files) >= 3:  # Limit to 3 similar files
                        break
        
        return similar_files