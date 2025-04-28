import React from 'react';

const PromptInput = ({ value, onChange, onSubmit, isLoading }) => {
  return (
    <div className="prompt-input-container">
      <h2>Improvement Prompt</h2>
      <textarea
        className="prompt-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Describe how you want the code to be improved..."
        rows={4}
      />
      <button 
        className="submit-button" 
        onClick={onSubmit}
        disabled={isLoading}
      >
        {isLoading ? 'Processing...' : 'Improve Code'}
      </button>
    </div>
  );
};

export default PromptInput;