import React from 'react';

interface MainLayoutProps {
  children: React.ReactNode;
  sidebarContent: React.ReactNode;
  headerContent: React.ReactNode;
  interactionContent: React.ReactNode;
}

export function MainLayout({ 
  children, 
  sidebarContent, 
  headerContent, 
  interactionContent 
}: MainLayoutProps) {
  return (
    <div className="app-container">
      {/* Left Navigation / History Area */}
      <aside className="sidebar">
        {sidebarContent}
      </aside>

      {/* Main Learning Workspace */}
      <main className="main-content">
        {/* Student State Header */}
        <header className="header">
          {headerContent}
        </header>

        {/* AI Teacher Unified Workspace */}
        <div className="teaching-workspace">
          {children}
        </div>

        {/* Question & Answer Interaction Area */}
        <section className="interaction-area">
          {interactionContent}
        </section>
      </main>
    </div>
  );
}
