from flask import Flask, request, jsonify
import json
# from utils import *
from flask_cors import CORS, cross_origin
from agents import *
from masteragent import AgenticAISystem
import uuid 
import shutil
import difflib

app = Flask(__name__)
cors = CORS(app, resources={
    r"/*":{
        "origins":"*"
    }
})
# orchestrator = OrchestratorAgent()

# @app.route('/chat', methods=['POST'])
# @cross_origin()
# def chat_endpoint():
#     """Single API endpoint for the code improvement system."""
#     data = request.json
    
#     if not data or 'code' not in data or 'prompt' not in data:
#         return jsonify({"error": "Missing required fields: 'code' and 'prompt'"})
    
#     try:
#         result = orchestrator.process({
#             "code": data['code'],
#             "prompt": data['prompt']
#         })
#         response = {
#             "original_code": result.get("original_code", ""),
#             "improved_code": result.get("improved_code", ""),
#             "explanation": result.get("explanation", ""),
#             "language": result.get("language", "unknown"),
#             "can_integrate": True
#         }
        
#         return jsonify(response)
    
#     except Exception as e:
#         logger.error(f"Error processing request: {str(e)}")
#         return jsonify({"error": f"Failed to process request: {str(e)}"})

class ChangeStore:
    def __init__(self):
        self.store_dir = r"F:\Cursor-Clone\Backend\pending_changes"
        self.original_files_dir = r"F:\Cursor-Clone\Backend\original_files"
        os.makedirs(r"F:\Cursor-Clone\Backend\pending_changes", exist_ok=True)
    
    def save_change(self, change_id, change_data):
        """Save change data to disks"""
        file_path = os.path.join(r"F:\Cursor-Clone\Backend\pending_changes", f"{change_id}.json")
        try:
            with open(file_path, 'w+') as f:
                json.dump(change_data, f)
            return True
        except Exception as e:
            logger.error(f"Error saving change {change_id}: {e}")
            return False
    
    def get_change(self, change_id):
        """Get a pending change by ID"""
        try:
            file_path = os.path.join(r"F:\Cursor-Clone\Backend\pending_changes", f"{change_id}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error loading change {change_id}: {e}")
            return None
    def backup_original_files(self, repo_path):
        """Backup original files before making changes"""
        backup_dir = self.original_files_dir
        os.makedirs(backup_dir, exist_ok=True)
        
        backed_up_files = []
        for file_path in os.listdir(repo_path):
            if '.git' not in file_path:
                full_path = os.path.join(repo_path, file_path)
                if os.path.exists(full_path):
                    backup_file_dir = os.path.dirname(os.path.join(backup_dir, file_path))
                    os.makedirs(backup_file_dir, exist_ok=True)
                    shutil.copy2(full_path, os.path.join(backup_dir, file_path))
                    backed_up_files.append(file_path)
        
        return backed_up_files
    
    def get_original_file_content(self, file_path):
        """Get original content of a backed up file"""
        backup_file_path = os.path.join(self.original_files_dir, file_path)
        if os.path.exists(backup_file_path):
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
        
change_store = ChangeStore()

@app.route('/chatv1',methods=['GET','POST'])
@cross_origin()
def chat_endpoint_v2():
    data = request.json
    if not data or 'repo_path' not in data or 'prompt' not in data:
        return jsonify({"error": "Missing required fields: 'repo_path' and 'prompt'"})
    try:
        if 'index_path' in data:
            cursor = AgenticAISystem(repo_path=data['repo_path'],index_path=data['index_path'])
        cursor = AgenticAISystem(repo_path=data['repo_path'])
        backed_up_files = change_store.backup_original_files(data['repo_path'])
        results = cursor.process_requirement(requirement=data['prompt'])

        namespace = uuid.NAMESPACE_DNS
        name_uuid_sha1 = uuid.uuid5(namespace, f"{data['prompt']}")
        results['change_id'] = str(name_uuid_sha1)
        results['backed_up_files'] = backed_up_files
        change_store.save_change(name_uuid_sha1, {
            'repo_path': data['repo_path'],
            'index_path': data.get('index_path'),
            'requirement': data['prompt'],
            'branch_name': data.get('branch_name'),
            'results': results,
            'backed_up_files': backed_up_files
        })
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": f"Failed to process request: {str(e)}"})


@app.route('/accept_changes',methods=['GET','POST'])
@cross_origin()
def accept_changes():
    data = request.json
    if not data or 'change_id' not in data:
        return jsonify({"error": "Missing required field: 'change_id'"})
    
    try:
        change_id = data['change_id']
        change_data = change_store.get_change(change_id)
        
        if not change_data:
            return jsonify({"error": f"Change ID {change_id} not found"})
        vcs = VCSIntegrator(
            repo_path=change_data['repo_path']
        )
        results = change_data['results']
        plan = results.get('plan', {})
        changes = results.get('changes', {})
        commit_message = data.get('commit_message')
        if not commit_message:
            commit_message = vcs.generate_commit_message(plan, changes)
        commit_success = vcs.commit_changes(commit_message)
        vcs_results = {
            "change_id": change_id,
            "commit_success": commit_success,
            "commit_message": commit_message
        }
        
        return jsonify(vcs_results)
    except Exception as e:
        logger.error(f"Error accepting changes: {str(e)}")
        return jsonify({"error": f"Failed to accept changes: {str(e)}"})


@app.route('/pending_changes', methods=['GET'])
@cross_origin()
def list_pending_changes():
    try:
        pending_changes = []
        for filename in os.listdir(change_store.store_dir):
            if filename.endswith('.json'):
                change_id = filename.split('.')[0]
                change_data = change_store.get_change(change_id)
                if change_data:
                    pending_changes.append({
                        "change_id": change_id,
                        "requirement": change_data["requirement"],
                        "repo_path": change_data["repo_path"],
                        "branch_name": change_data.get("branch_name"),
                        "test_success": change_data["results"].get("test_results", {}).get("success", False)
                    })
        
        return jsonify({"pending_changes": pending_changes})
    except Exception as e:
        logger.error(f"Error listing pending changes: {str(e)}")
        return jsonify({"error": f"Failed to list pending changes: {str(e)}"})
    

@app.route('/get_file_changes', methods=['POST'])
@cross_origin()
def get_file_changes():
    data = request.json
    if not data or 'change_id' not in data:
        return jsonify({"error": "Missing required field: 'change_id'"})
    change_id = data['change_id']
    change_data = change_store.get_change(change_id)
    
    if not change_data:
        return jsonify({"error": f"Change ID {change_id} not found"})
    
    repo_path = change_data['repo_path']
    results = change_data['results']
    changes = results.get('changes', {})
    
    file_changes = {}
    
    # Get changes for modified files
    modified_files = changes.get('modified_files', [])
    for file_path in modified_files:
        # Get original content
        original_content = change_store.get_original_file_content(file_path)
        
        # Get current content
        current_file_path = os.path.join(repo_path, file_path)
        current_content = None
        if os.path.exists(current_file_path):
            with open(current_file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
        
        # Generate diff
        if original_content and current_content:
            original_lines = original_content.splitlines()
            current_lines = current_content.splitlines()
            diff = list(difflib.unified_diff(
                original_lines, 
                current_lines,
                fromfile=f'a/{file_path}',
                tofile=f'b/{file_path}',
                lineterm=''
            ))
            
            file_changes[file_path] = {
                'original': original_content,
                'current': current_content,
                'diff': '\n'.join(diff)
            }
    
    # Get content for created files
    created_files = changes.get('created_files', [])
    for file_path in created_files:
        current_file_path = os.path.join(repo_path, file_path)
        if os.path.exists(current_file_path):
            with open(current_file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
                
            file_changes[file_path] = {
                'original': None,
                'current': current_content,
                'diff': f'New file: {file_path}\n\n{current_content}'
            }
    
    return jsonify({
        "change_id": change_id,
        "file_changes": file_changes
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)