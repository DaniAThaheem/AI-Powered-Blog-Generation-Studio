import React from 'react';
import { PageHeader } from '../components/shared/PageHeader';
import { MediaGallery } from '../features/media/MediaGallery';

export const MediaPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Media Library"
        description="Generated figures, flowcharts, and architecture diagrams stored in Cloudinary"
      />
      <MediaGallery />
    </div>
  );
};
export default MediaPage;
