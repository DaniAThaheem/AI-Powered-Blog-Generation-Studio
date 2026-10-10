import React from 'react';
import { useParams } from 'react-router-dom';
import { BlogDetails } from '../features/blogs/BlogDetails';

export const BlogDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  if (!id) {
    return <div className="p-8 text-center text-xs text-red-400">Blog ID is required</div>;
  }

  return <BlogDetails generationId={id} />;
};
export default BlogDetailsPage;
