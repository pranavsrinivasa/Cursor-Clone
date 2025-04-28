import React from 'react';

const Header = () => {
  return (
    <header className="header">
      <div className="logo">
        <h1>CodeImprover</h1>
      </div>
      <nav>
        <ul>
          <li>
            <a href="/" className="active">Home</a>
          </li>
          <li>
            <a href="/about">About</a>
          </li>
          <li>
            <a href="/docs">Docs</a>
          </li>
        </ul>
      </nav>
    </header>
  );
};

export default Header;