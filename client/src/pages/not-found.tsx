export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-100">
      <h1 className="text-4xl font-bold mb-4">404</h1>
      <p className="text-slate-400">Page not found</p>
      <a href="/" className="mt-4 text-cyan-400 hover:text-cyan-300">
        Return to Dashboard
      </a>
    </div>
  )
}
