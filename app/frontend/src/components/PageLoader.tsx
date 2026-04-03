export default function PageLoader() {
  return (
    <div className="flex justify-center py-20" role="status" aria-label="Loading">
      <div className="animate-spin w-8 h-8 border-2 border-brand border-t-transparent rounded-full" />
      <span className="sr-only">Loading...</span>
    </div>
  );
}
