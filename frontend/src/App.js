import React, { useState } from 'react';
import Header from './components/Header';
import CodeEditor from './components/CodeEditor';
import PromptInput from './components/PromptInput';
import ResultView from './components/ResultView';
import { improveCode, acceptChanges } from './api';
import './styles.css';
import ResultView2 from './components/ResultView2';

function App() {
  const [code, setCode] = useState('// Enter your code here...');
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    if (!code.trim() || !prompt.trim()) {
      setError('Both code and improvement prompt are required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await improveCode(code, prompt);
      setResult(response);
    } catch (err) {
      setError(err.message || 'Failed to improve code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <div className="input-section">
          <h2>Input Repo Path</h2>
          <CodeEditor 
            value={code} 
            onChange={setCode} 
            placeholder="Enter Repo Path"
          />
          
          <PromptInput 
            value={prompt} 
            onChange={setPrompt} 
            onSubmit={handleSubmit}
            isLoading={loading}
          />
          
          {error && <p className="error-message">{error}</p>}
        </div>
        
        {result && (
          <div className="result-section">
            <ResultView2 result={result} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;