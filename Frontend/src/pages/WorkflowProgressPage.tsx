import React from 'react';
import { useParams } from 'react-router-dom';
import { WorkflowMonitor } from '../features/workflow/WorkflowMonitor';

export const WorkflowProgressPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  if (!id) {
    return <div className="p-8 text-center text-xs text-red-400">Generation ID is required</div>;
  }

  return <WorkflowMonitor generationId={id} />;
};
export default WorkflowProgressPage;
