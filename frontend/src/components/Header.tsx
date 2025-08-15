import React from 'react';
import { Brain } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Header: React.FC = () => {
  return (
    <header className="border-b border-gray-700 bg-gray-900 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-center">
          <Link to="/" className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-blue-500 shadow-lg">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">
              AI Assistant
            </h1>
          </Link>
        </div>
      </div>
    </header>
  );
};