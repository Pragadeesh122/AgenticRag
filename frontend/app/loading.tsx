export default function HomeLoading() {
  return (
    <div className='flex h-screen w-screen overflow-hidden bg-[#1a1a1a]'>
      {/* Skeleton Sidebar */}
      <div className='w-[260px] h-full shrink-0 border-r border-white/5 bg-[#1e1e1e] flex flex-col p-4'>
        {/* Logo */}
        <div className='flex items-center gap-2.5 mb-6'>
          <div className='h-7 w-7 bg-white/5 rounded-lg animate-pulse'></div>
          <div className='h-4 w-24 bg-white/5 rounded-md animate-pulse'></div>
        </div>
        {/* Projects label */}
        <div className='h-3 w-16 bg-white/5 rounded mb-3 animate-pulse'></div>
        <div className='flex flex-col gap-1.5 mb-4'>
          <div className='h-10 w-full bg-white/5 rounded-lg animate-pulse'></div>
          <div className='h-10 w-full bg-white/5 rounded-lg animate-pulse'></div>
        </div>
        <div className='border-t border-white/5 mb-4'></div>
        {/* Session list */}
        <div className='h-3 w-12 bg-white/5 rounded mb-3 animate-pulse'></div>
        <div className='flex flex-col gap-1.5'>
          <div className='h-10 w-full bg-white/5 rounded-lg animate-pulse'></div>
          <div className='h-10 w-full bg-white/5 rounded-lg animate-pulse'></div>
          <div className='h-10 w-[85%] bg-white/5 rounded-lg animate-pulse'></div>
        </div>
      </div>

      {/* Skeleton Main Content */}
      <main className='flex flex-col flex-1 min-w-0 min-h-0'>
        {/* Skeleton Header */}
        <header className='flex items-center gap-2 px-4 py-3 shrink-0 border-b border-white/5'>
          <div className='h-8 w-8 bg-white/5 rounded-lg animate-pulse'></div>
          <div className='flex-1 flex justify-center'>
            <div className='h-4 w-32 bg-white/5 rounded-full animate-pulse'></div>
          </div>
          <div className='h-8 w-8 bg-white/5 rounded-lg animate-pulse'></div>
          <div className='h-8 w-8 bg-white/5 rounded-full animate-pulse'></div>
        </header>

        {/* Skeleton Chat Area */}
        <div className='flex-1 flex flex-col items-center justify-center p-4'>
          <div className='flex flex-col items-center gap-3 animate-pulse'>
            <div className='h-12 w-12 bg-white/5 rounded-xl'></div>
            <div className='h-4 w-48 bg-white/5 rounded-full'></div>
          </div>
        </div>

        {/* Skeleton Input */}
        <div className='w-full max-w-3xl mx-auto px-4 pb-6 animate-pulse'>
          <div className='h-14 w-full bg-white/5 rounded-2xl border border-white/10'></div>
        </div>
      </main>
    </div>
  );
}
