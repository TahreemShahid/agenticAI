import React from 'react';
import { Brain, FileText, Zap, GitCompare } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';

export const Header: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'PDF Q&A', icon: FileText },
    { path: '/summarize', label: 'Text Summarize', icon: Zap },
    { path: '/compare', label: 'AI Compare', icon: GitCompare },
  ];

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-r from-primary to-primary-glow shadow-glow">
              <Brain className="h-6 w-6 text-primary-foreground" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-primary-glow bg-clip-text text-transparent">
              IntelliText
            </h1>
          </Link>
          
          <nav className="flex items-center gap-1">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                  location.pathname === path
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
};