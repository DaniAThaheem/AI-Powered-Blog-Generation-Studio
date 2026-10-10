import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'outline';
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className = '',
}) => {
  const base = 'inline-flex items-center font-medium rounded-full';

  const variants = {
    default: 'bg-surface-elevated text-text-secondary border border-border/50',
    success: 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60',
    warning: 'bg-amber-950/60 text-amber-400 border border-amber-800/60',
    danger: 'bg-red-950/60 text-red-400 border border-red-800/60',
    info: 'bg-cyan-950/60 text-cyan-400 border border-cyan-800/60',
    outline: 'border border-border text-text-secondary',
  };

  const sizes = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
  };

  return (
    <span className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}>
      {children}
    </span>
  );
};
