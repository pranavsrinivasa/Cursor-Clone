import React from 'react';

const CodeEditor = ({ value, onChange, placeholder }) => {
  return (
    <div className="code-editor-container">
      <textarea
        className="code-editor"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={1}
      />
    </div>
  );
};

export default CodeEditor;