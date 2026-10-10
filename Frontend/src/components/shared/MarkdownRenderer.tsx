import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import { CopyButton } from './EmptyState';
import { ImageOff } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const ImageWithFallback: React.FC<{ src?: string; alt?: string }> = ({ src, alt }) => {
  const [hasError, setHasError] = useState(false);

  if (!src || hasError) {
    return (
      <span className="my-4 flex items-center gap-2 p-3 bg-surface-elevated/70 border border-border/60 rounded-lg text-xs text-text-secondary">
        <ImageOff className="w-4 h-4 text-text-muted" />
        <span>Image unavailable: {alt || 'Illustration'}</span>
      </span>
    );
  }

  return (
    <figure className="my-6">
      <img
        src={src}
        alt={alt || 'Blog illustration'}
        loading="lazy"
        onError={() => setHasError(true)}
        className="rounded-xl border border-border/60 shadow-lg max-h-[500px] w-auto mx-auto object-contain bg-surface/30"
      />
      {alt && (
        <figcaption className="text-center text-xs text-text-muted mt-2 italic">
          {alt}
        </figcaption>
      )}
    </figure>
  );
};

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  return (
    <div className={`prose prose-invert max-w-none text-text-primary text-sm leading-relaxed ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary mt-8 mb-4 border-b border-border/40 pb-3 tracking-tight">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-xl sm:text-2xl font-bold text-text-primary mt-8 mb-3 tracking-tight flex items-center gap-2">
              <span className="w-1.5 h-5 rounded-full bg-primary" />
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-lg font-semibold text-text-primary mt-6 mb-2">{children}</h3>
          ),
          p: ({ children }) => <p className="mb-4 text-text-secondary leading-7">{children}</p>,
          ul: ({ children }) => <ul className="list-disc list-inside mb-4 space-y-1.5 text-text-secondary">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal list-inside mb-4 space-y-1.5 text-text-secondary">{children}</ol>,
          li: ({ children }) => <li className="leading-6">{children}</li>,
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-cyan-500/70 bg-cyan-950/20 px-4 py-3 rounded-r-lg my-4 text-text-secondary italic">
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-6 border border-border/60 rounded-lg">
              <table className="w-full text-left text-xs border-collapse">{children}</table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-surface-elevated border-b border-border text-text-primary">{children}</thead>
          ),
          th: ({ children }) => <th className="p-3 font-semibold">{children}</th>,
          td: ({ children }) => <td className="p-3 border-b border-border/40 text-text-secondary">{children}</td>,
          code: ({ inline, className: codeClass, children, ...props }: any) => {
            const codeString = String(children).replace(/\n$/, '');
            if (inline) {
              return (
                <code className="bg-surface-elevated text-cyan-400 font-mono text-xs px-1.5 py-0.5 rounded border border-border/40">
                  {children}
                </code>
              );
            }
            return (
              <div className="relative my-4 rounded-xl border border-border/60 bg-surface-muted/90 overflow-hidden shadow-inner group">
                <div className="flex items-center justify-between px-4 py-1.5 bg-surface-elevated/80 border-b border-border/40 text-[11px] text-text-muted font-mono">
                  <span>code</span>
                  <CopyButton text={codeString} label="Copy" className="text-[10px] py-1 px-2 h-6" />
                </div>
                <pre className="p-4 overflow-x-auto text-xs font-mono leading-relaxed text-text-primary">
                  <code>{children}</code>
                </pre>
              </div>
            );
          },
          img: ({ src, alt }) => <ImageWithFallback src={src} alt={alt} />,
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2 transition-colors font-medium"
            >
              {children}
            </a>
          ),
          hr: () => <hr className="my-8 border-border/40" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
