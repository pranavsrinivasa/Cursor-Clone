import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import './ResultView.css'
const ResultView2 = ({ result }) => {
  const [activeTab, setActiveTab] = useState('plan');
  const [acceptingChanges, setAcceptingChanges] = useState(false);
  const [commitMessage, setCommitMessage] = useState('');
  const [fileChanges, setFileChanges] = useState(null);
  const [changesLoading, setChangesLoading] = useState(false);
  const [activeChangeFile, setActiveChangeFile] = useState('');
  const [diffViewMode, setDiffViewMode] = useState('diff');

  const handleAcceptChanges = async () => {
    if (!result.change_id) {
      toast.error('No change ID available');
      return;
    }
    
    try {
      setAcceptingChanges(true);
      const response = await fetch('http://localhost:5000/accept_changes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          change_id: result.change_id,
          commit_message: commitMessage || undefined
        }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to accept changes');
      }
      
      toast.success('Changes successfully committed!');
    } catch (error) {
      toast.error(`Error: ${error.message}`);
    } finally {
      setAcceptingChanges(false);
    }
  };

  useEffect(() => {
    const fetchFileChanges = async () => {
      if (activeTab === 'git-blame' && result.change_id && !fileChanges) {
        setChangesLoading(true);
        try {
          const response = await fetch('http://localhost:5000/get_file_changes', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              change_id: result.change_id
            }),
          });
          
          const data = await response.json();
          
          if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch file changes');
          }
          
          setFileChanges(data.file_changes);
          
          // Set the first file as active if available
          const fileNames = Object.keys(data.file_changes || {});
          if (fileNames.length > 0) {
            setActiveChangeFile(fileNames[0]);
          }
        } catch (error) {
          toast.error(`Error fetching file changes: ${error.message}`);
        } finally {
          setChangesLoading(false);
        }
      }
    };
    
    fetchFileChanges();
  }, [activeTab, result.change_id, fileChanges]);
  
  const highlightDiff = (diffText) => {
    if (!diffText) return null;
    
    return diffText.split('\n').map((line, index) => {
      let className = '';
      if (line.startsWith('+')) {
        className = 'diff-added';
      } else if (line.startsWith('-')) {
        className = 'diff-removed';
      } else if (line.startsWith('@@')) {
        className = 'diff-hunk-header';
      }
      
      return (
        <div key={index} className={className}>
          {line}
        </div>
      );
    });
  };

  const renderDiffContent = () => {
    if (!activeChangeFile || !fileChanges || !fileChanges[activeChangeFile]) {
      return <p>Select a file to view changes</p>;
    }
    
    const fileChange = fileChanges[activeChangeFile];
    
    switch (diffViewMode) {
      case 'diff':
        return (
          <pre className="diff-display">
            {highlightDiff(fileChange.diff)}
          </pre>
        );
      case 'original':
        return fileChange.original ? (
          <pre className="code-display">
            <code>{fileChange.original}</code>
          </pre>
        ) : (
          <p>No original content (new file)</p>
        );
      case 'current':
        return (
          <pre className="code-display">
            <code>{fileChange.current}</code>
          </pre>
        );
      default:
        return null;
    }
  };

  const renderJsonObject = (obj) => {
    return (
      <pre className="code-display">
        <code>{JSON.stringify(obj, null, 2)}</code>
      </pre>
    );
  };

  const testsPassed = result?.test_results?.success;

  const renderContent = () => {
    switch (activeTab) {
      case 'plan':
        return (
          <div className="plan-content">
            <h3>Implementation Plan</h3>
            {result.plan ? (
              <>
                <h4>Files to Modify</h4>
                <ul>
                  {result.plan.files_to_modify?.map((file, index) => (
                    <li key={`mod-${index}`}>{file}</li>
                  )) || <li>None</li>}
                </ul>
                
                <h4>Files to Create</h4>
                <ul>
                  {result.plan.files_to_create?.map((file, index) => (
                    <li key={`create-${index}`}>{file}</li>
                  )) || <li>None</li>}
                </ul>
                
                <h4>Implementation Steps</h4>
                <ol>
                  {result.plan.implementation_steps?.map((step, index) => (
                    <li key={`step-${index}`}>{step}</li>
                  )) || <li>No steps provided</li>}
                </ol>
                
                <h4>Potential Risks</h4>
                <ul>
                  {result.plan.potential_risks?.map((risk, index) => (
                    <li key={`risk-${index}`}>{risk}</li>
                  )) || <li>No risks identified</li>}
                </ul>
              </>
            ) : (
              <p>No plan available</p>
            )}
          </div>
        );
      
      case 'changes':
        return (
          <div className="changes-content">
            <h3>Implemented Changes</h3>
            {result.changes ? (
              <>
                <h4>Modified Files</h4>
                <ul>
                  {result.changes.modified_files?.map((file, index) => (
                    <li key={`mod-${index}`}>{file}</li>
                  )) || <li>No files modified</li>}
                </ul>
                
                <h4>Created Files</h4>
                <ul>
                  {result.changes.created_files?.map((file, index) => (
                    <li key={`create-${index}`}>{file}</li>
                  )) || <li>No files created</li>}
                </ul>
                
                {result.changes.errors?.length > 0 && (
                  <>
                    <h4>Errors</h4>
                    <ul className="error-list">
                      {result.changes.errors.map((error, index) => (
                        <li key={`error-${index}`}>{error}</li>
                      ))}
                    </ul>
                  </>
                )}
              </>
            ) : (
              <p>No changes available</p>
            )}
          </div>
        );
      
      case 'tests':
        return (
          <div className="tests-content">
            <h3>Test Results</h3>
            {result.test_results ? (
              <>
                <div className={`test-status ${testsPassed ? 'success' : 'failure'}`}>
                  <span className="status-indicator"></span>
                  <span className="status-text">
                    {testsPassed ? 'All tests passed!' : 'Tests failed'}
                  </span>
                </div>
                
                {!testsPassed && result.test_analysis && (
                  <div className="test-analysis">
                    <h4>Test Analysis</h4>
                    <p><strong>Summary:</strong> {result.test_analysis.summary}</p>
                    
                    <h5>Root Causes</h5>
                    <ul>
                      {result.test_analysis.root_causes?.map((cause, index) => (
                        <li key={`cause-${index}`}>{cause}</li>
                      ))}
                    </ul>
                    
                    <h5>Suggested Fixes</h5>
                    <div className="suggested-fixes">
                      {result.test_analysis.fixes?.map((fix, index) => (
                        <div className="fix-item" key={`fix-${index}`}>
                          <p><strong>File:</strong> {fix.file}</p>
                          <p><strong>Issue:</strong> {fix.issue}</p>
                          <p><strong>Fix:</strong> {fix.fix}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <h4>Test Output</h4>
                <pre className="test-output">
                  <code>{result.test_results.output}</code>
                </pre>
                
                {result.test_results.error && (
                  <>
                    <h4>Error Output</h4>
                    <pre className="test-error">
                      <code>{result.test_results.error}</code>
                    </pre>
                  </>
                )}
              </>
            ) : (
              <p>No test results available</p>
            )}
          </div>
        );
      
      case 'generated-tests':
        return (
          <div className="generated-tests-content">
            <h3>Generated Tests</h3>
            {result.tests?.generated_tests?.length > 0 ? (
              <ul>
                {result.tests.generated_tests.map((test, index) => (
                  <li key={`test-${index}`}>{test}</li>
                ))}
              </ul>
            ) : (
              <p>No tests were generated</p>
            )}
          </div>
        );
      
      case 'raw':
        return (
          <div className="raw-content">
            <h3>Raw Results</h3>
            {renderJsonObject(result)}
          </div>
        );
      
      case 'git-blame':
      return (
        <div className="git-blame-content">
          <h3>File Changes</h3>
          {changesLoading ? (
            <p>Loading file changes...</p>
          ) : fileChanges ? (
            <div className="changes-container">
              <div className="changes-sidebar">
                <h4>Files</h4>
                <ul>
                  {Object.keys(fileChanges).map((file, index) => (
                    <li 
                      key={`change-file-${index}`}
                      className={activeChangeFile === file ? 'active-change-file' : ''}
                      onClick={() => setActiveChangeFile(file)}
                    >
                      {file}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="changes-content">
                <div className="changes-header">
                  <h4>{activeChangeFile}</h4>
                  <div className="view-toggle">
                    <button 
                      className={`view-toggle-btn ${diffViewMode === 'diff' ? 'active' : ''}`}
                      onClick={() => setDiffViewMode('diff')}
                    >
                      Diff
                    </button>
                    <button 
                      className={`view-toggle-btn ${diffViewMode === 'original' ? 'active' : ''}`}
                      onClick={() => setDiffViewMode('original')}
                    >
                      Original
                    </button>
                    <button 
                      className={`view-toggle-btn ${diffViewMode === 'current' ? 'active' : ''}`}
                      onClick={() => setDiffViewMode('current')}
                    >
                      Current
                    </button>
                  </div>
                </div>
                <div className="diff-content">
                  {renderDiffContent()}
                </div>
              </div>
            </div>
          ) : (
            <p>No file changes available.</p>
          )}
        </div>
      );
    
      default:
        return null;
    }
  };

  return (
    <div className="result-view">
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'plan' ? 'active' : ''}`}
          onClick={() => setActiveTab('plan')}
        >
          Plan
        </button>
        <button 
          className={`tab ${activeTab === 'changes' ? 'active' : ''}`}
          onClick={() => setActiveTab('changes')}
        >
          Changes
        </button>
        <button 
          className={`tab ${activeTab === 'tests' ? 'active' : ''}`}
          onClick={() => setActiveTab('tests')}
        >
          Test Results
        </button>
        <button 
          className={`tab ${activeTab === 'generated-tests' ? 'active' : ''}`}
          onClick={() => setActiveTab('generated-tests')}
        >
          Generated Tests
        </button>
        <button 
          className={`tab ${activeTab === 'git-blame' ? 'active' : ''}`}
          onClick={() => setActiveTab('git-blame')}
        >
          File Changes
        </button>
        <button 
          className={`tab ${activeTab === 'raw' ? 'active' : ''}`}
          onClick={() => setActiveTab('raw')}
        >
          Raw Data
        </button>
      </div>
      <div className="tab-content">
        {renderContent()}
      </div>
      <div className="commit-section">
        <h3>Version Control Integration</h3>
        <div className="commit-controls">
          <div className="commit-message-input">
            <label htmlFor="commit-message">Commit Message:</label>
            <textarea 
              id="commit-message"
              placeholder="Enter commit message (optional)"
              value={commitMessage}
              onChange={(e) => setCommitMessage(e.target.value)}
              rows={3}
            />
          </div>
          <button 
            className={`commit-button`}
            onClick={handleAcceptChanges}
          >
            {acceptingChanges ? 'Committing...' : 'Commit Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ResultView2;