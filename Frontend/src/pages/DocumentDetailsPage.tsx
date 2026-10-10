import React from 'react';
import { useParams } from 'react-router-dom';
import { DocumentDetails } from '../features/documents/DocumentDetails';

export const DocumentDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  if (!id) {
    return <div className="p-8 text-center text-xs text-red-400">Document ID is required</div>;
  }

  return <DocumentDetails documentId={id} />;
};
export default DocumentDetailsPage;
