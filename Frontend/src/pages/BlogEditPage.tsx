import React from 'react';
import { useParams } from 'react-router-dom';
import { BlogEditor } from '../features/blogs/BlogEditor';

export const BlogEditPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  if (!id) {
    return <div className="p-8 text-center text-xs text-red-400">Blog ID is required</div>;
  }

  return <BlogEditor generationId={id} />;
};
export default BlogEditPage;
