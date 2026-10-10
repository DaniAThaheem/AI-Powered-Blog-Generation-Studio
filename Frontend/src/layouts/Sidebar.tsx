import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  PenTool,
  BookOpen,
  FileText,
  MessageSquare,
  Image as ImageIcon,
  History,
  Settings as SettingsIcon,
  Sparkles,
  ChevronRight,
} from 'lucide-react';

interface SidebarProps {
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onCloseMobile }) => {
  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/generate', label: 'New Generation', icon: PenTool, badge: 'AI' },
    { to: '/blogs', label: 'My Blogs', icon: BookOpen },
    { to: '/documents', label: 'Reference Library', icon: FileText },
    { to: '/chat', label: 'CV / Doc Chatbot', icon: MessageSquare },
    { to: '/media', label: 'Media Library', icon: ImageIcon },
    { to: '/history', label: 'Execution History', icon: History },
    { to: '/settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <aside className="w-64 h-full bg-surface border-r border-border/60 flex flex-col select-none">
      {/* Brand header */}
      <div className="p-5 border-b border-border/50 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-primary to-accent flex items-center justify-center text-white shadow-md shadow-primary/25">
          <Sparkles className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-sm font-bold text-text-primary tracking-tight flex items-center gap-1.5">
            Blog Studio
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-primary/20 text-cyan-400 font-normal">v2.0</span>
          </h2>
          <p className="text-[11px] text-text-muted">LangGraph Multi-Agent</p>
        </div>
      </div>

      {/* Navigation list */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
          Studio Workspace
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onCloseMobile}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all group ${
                  isActive
                    ? 'bg-primary/15 text-white font-semibold border-l-2 border-primary shadow-sm'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated/70'
                }`
              }
            >
              <div className="flex items-center gap-2.5">
                <Icon className="w-4 h-4 text-text-secondary group-hover:text-cyan-400 transition-colors" />
                <span>{item.label}</span>
              </div>
              {item.badge ? (
                <span className="text-[10px] font-mono font-semibold px-1.5 py-0.2 rounded bg-primary text-white">
                  {item.badge}
                </span>
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* System status pill footer */}
      <div className="p-3 border-t border-border/50">
        <div className="p-2.5 rounded-lg bg-surface-muted/60 border border-border/40 text-[11px] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-text-secondary">LangGraph Engine</span>
          </div>
          <span className="text-[10px] font-mono text-cyan-400">Active</span>
        </div>
      </div>
    </aside>
  );
};
