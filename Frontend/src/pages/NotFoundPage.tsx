import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Home, ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="p-4 rounded-2xl bg-surface border border-border/60 text-cyan-400 font-mono font-bold text-4xl mb-4 shadow-lg">
        404
      </div>
      <h2 className="text-xl font-bold text-text-primary mb-2">Page Not Found</h2>
      <p className="text-xs text-text-secondary max-w-sm mb-6">
        The studio page or resource you are looking for does not exist or has been moved.
      </p>
      <div className="flex items-center gap-3">
        <Button variant="secondary" size="sm" onClick={() => navigate(-1)} leftIcon={<ArrowLeft className="w-3.5 h-3.5" />}>
          Go Back
        </Button>
        <Button variant="primary" size="sm" onClick={() => navigate('/dashboard')} leftIcon={<Home className="w-3.5 h-3.5" />}>
          Return to Dashboard
        </Button>
      </div>
    </div>
  );
};
export default NotFoundPage;
