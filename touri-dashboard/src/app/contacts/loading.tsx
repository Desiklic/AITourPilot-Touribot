export default function Loading() {
  return (
    <div className="p-6 space-y-4">
      <div className="h-8 w-36 bg-muted animate-pulse rounded" />
      <div className="h-5 w-48 bg-muted animate-pulse rounded" />
      <div className="flex gap-2 mt-2 flex-wrap">
        <div className="h-9 w-64 bg-muted animate-pulse rounded" />
        <div className="h-9 w-20 bg-muted animate-pulse rounded" />
        <div className="h-9 w-20 bg-muted animate-pulse rounded" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
        {Array.from({ length: 9 }).map((_, i) => (
          <div key={i} className="h-44 bg-muted animate-pulse rounded-lg" />
        ))}
      </div>
    </div>
  );
}
