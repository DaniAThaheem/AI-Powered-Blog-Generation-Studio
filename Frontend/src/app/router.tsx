import React, { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppShell } from '../layouts/AppShell';

// Lazy-loaded route pages for small initial bundle size
const DashboardPage = lazy(() => import('../pages/DashboardPage'));
const GeneratePage = lazy(() => import('../pages/GeneratePage'));
const WorkflowProgressPage = lazy(() => import('../pages/WorkflowProgressPage'));
const BlogsPage = lazy(() => import('../pages/BlogsPage'));
const BlogDetailsPage = lazy(() => import('../pages/BlogDetailsPage'));
const BlogEditPage = lazy(() => import('../pages/BlogEditPage'));
const DocumentsPage = lazy(() => import('../pages/DocumentsPage'));
const DocumentDetailsPage = lazy(() => import('../pages/DocumentDetailsPage'));
const MediaPage = lazy(() => import('../pages/MediaPage'));
const HistoryPage = lazy(() => import('../pages/HistoryPage'));
const ChatPage = lazy(() => import('../pages/ChatPage'));
const SettingsPage = lazy(() => import('../pages/SettingsPage'));
const NotFoundPage = lazy(() => import('../pages/NotFoundPage'));

const PageLoader = () => (
  <div className="p-12 text-center text-xs text-text-muted flex items-center justify-center gap-2">
    <div className="w-4 h-4 rounded-full border-2 border-primary border-t-transparent animate-spin" />
    <span>Loading studio view...</span>
  </div>
);

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      {
        path: 'dashboard',
        element: (
          <Suspense fallback={<PageLoader />}>
            <DashboardPage />
          </Suspense>
        ),
      },
      {
        path: 'generate',
        element: (
          <Suspense fallback={<PageLoader />}>
            <GeneratePage />
          </Suspense>
        ),
      },
      {
        path: 'generations/:id/progress',
        element: (
          <Suspense fallback={<PageLoader />}>
            <WorkflowProgressPage />
          </Suspense>
        ),
      },
      {
        path: 'generations/:id',
        element: (
          <Suspense fallback={<PageLoader />}>
            <WorkflowProgressPage />
          </Suspense>
        ),
      },
      {
        path: 'blogs',
        element: (
          <Suspense fallback={<PageLoader />}>
            <BlogsPage />
          </Suspense>
        ),
      },
      {
        path: 'blogs/:id',
        element: (
          <Suspense fallback={<PageLoader />}>
            <BlogDetailsPage />
          </Suspense>
        ),
      },
      {
        path: 'blogs/:id/edit',
        element: (
          <Suspense fallback={<PageLoader />}>
            <BlogEditPage />
          </Suspense>
        ),
      },
      {
        path: 'documents',
        element: (
          <Suspense fallback={<PageLoader />}>
            <DocumentsPage />
          </Suspense>
        ),
      },
      {
        path: 'documents/:id',
        element: (
          <Suspense fallback={<PageLoader />}>
            <DocumentDetailsPage />
          </Suspense>
        ),
      },
      {
        path: 'media',
        element: (
          <Suspense fallback={<PageLoader />}>
            <MediaPage />
          </Suspense>
        ),
      },
      {
        path: 'history',
        element: (
          <Suspense fallback={<PageLoader />}>
            <HistoryPage />
          </Suspense>
        ),
      },
      {
        path: 'chat',
        element: (
          <Suspense fallback={<PageLoader />}>
            <ChatPage />
          </Suspense>
        ),
      },
      {
        path: 'settings',
        element: (
          <Suspense fallback={<PageLoader />}>
            <SettingsPage />
          </Suspense>
        ),
      },
      {
        path: '*',
        element: (
          <Suspense fallback={<PageLoader />}>
            <NotFoundPage />
          </Suspense>
        ),
      },
    ],
  },
]);
