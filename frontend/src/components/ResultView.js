// Old Frontend
// import React, { useState } from 'react';

// const ResultView = ({ result }) => {
//   const [activeTab, setActiveTab] = useState('improved');

//   const renderContent = () => {
//     switch (activeTab) {
//       case 'original':
//         return (
//           <pre className="code-display">
//             <code>{result.original_code}</code>
//           </pre>
//         );
//       case 'improved':
//         return (
//           <pre className="code-display">
//             <code>{result.improved_code}</code>
//           </pre>
//         );
//       case 'explanation':
//         return (
//           <div className="explanation">
//             <h3>Code Improvement Explanation</h3>
//             <p className="language-tag">Language: {result.language}</p>
//             <div className="explanation-content">
//               {result.explanation}
//             </div>
//           </div>
//         );
//       default:
//         return null;
//     }
//   };

//   return (
//     <div className="result-view">
//       <div className="tabs">
//         <button 
//           className={`tab ${activeTab === 'original' ? 'active' : ''}`}
//           onClick={() => setActiveTab('original')}
//         >
//           Original Code
//         </button>
//         <button 
//           className={`tab ${activeTab === 'improved' ? 'active' : ''}`}
//           onClick={() => setActiveTab('improved')}
//         >
//           Improved Code
//         </button>
//         <button 
//           className={`tab ${activeTab === 'explanation' ? 'active' : ''}`}
//           onClick={() => setActiveTab('explanation')}
//         >
//           Explanation
//         </button>
//       </div>
//       <div className="tab-content">
//         {renderContent()}
//       </div>
//     </div>
//   );
// };

// export default ResultView;