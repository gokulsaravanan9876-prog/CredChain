import { Card } from './ui'
import type { LucideIcon } from 'lucide-react'

export function Stub({ icon: Icon, title, description }: { icon: LucideIcon; title: string; description: string }) {
  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-ink">{title}</h1>
      <Card className="flex max-w-md flex-col items-center gap-3 p-10 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-canvas-2">
          <Icon className="h-5 w-5 text-faint" strokeWidth={1.75} />
        </div>
        <p className="text-sm text-muted">{description}</p>
      </Card>
    </div>
  )
}
