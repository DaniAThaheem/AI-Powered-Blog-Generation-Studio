import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, className = '', id, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-xs font-medium text-text-secondary mb-1.5">
            {label}
            {props.required && <span className="text-red-400 ml-0.5">*</span>}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`w-full bg-surface-elevated/70 border ${
            error ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : 'border-border focus:border-primary focus:ring-primary/20'
          } rounded-lg px-3.5 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 transition-all ${className}`}
          {...props}
        />
        {error ? (
          <p className="mt-1 text-xs text-red-400">{error}</p>
        ) : helperText ? (
          <p className="mt-1 text-xs text-text-muted">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = 'Input';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, helperText, className = '', id, ...props }, ref) => {
    const textareaId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={textareaId} className="block text-xs font-medium text-text-secondary mb-1.5">
            {label}
            {props.required && <span className="text-red-400 ml-0.5">*</span>}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          className={`w-full bg-surface-elevated/70 border ${
            error ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : 'border-border focus:border-primary focus:ring-primary/20'
          } rounded-lg px-3.5 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 transition-all resize-y ${className}`}
          {...props}
        />
        {error ? (
          <p className="mt-1 text-xs text-red-400">{error}</p>
        ) : helperText ? (
          <p className="mt-1 text-xs text-text-muted">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options: Array<{ value: string; label: string }>;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, helperText, options, className = '', id, ...props }, ref) => {
    const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={selectId} className="block text-xs font-medium text-text-secondary mb-1.5">
            {label}
            {props.required && <span className="text-red-400 ml-0.5">*</span>}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={`w-full bg-surface-elevated border ${
            error ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : 'border-border focus:border-primary focus:ring-primary/20'
          } rounded-lg px-3.5 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 transition-all ${className}`}
          {...props}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-surface text-text-primary">
              {opt.label}
            </option>
          ))}
        </select>
        {error ? (
          <p className="mt-1 text-xs text-red-400">{error}</p>
        ) : helperText ? (
          <p className="mt-1 text-xs text-text-muted">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

Select.displayName = 'Select';
