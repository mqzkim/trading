'use client';

import { Play } from 'lucide-react';
import { type FormEvent, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { usePipelineRun } from '@/hooks/use-pipeline';

export function PipelineRunForm() {
  const [symbols, setSymbols] = useState('');
  const [dryRun, setDryRun] = useState(false);
  const mutation = usePipelineRun();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const parsed = symbols
      .split(',')
      .map((s) => s.trim().toUpperCase())
      .filter(Boolean);
    mutation.mutate({ symbols: parsed, dry_run: dryRun });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="pipeline-symbols">Symbols</Label>
        <Input
          id="pipeline-symbols"
          placeholder="AAPL, MSFT, GOOGL... (empty = full universe)"
          value={symbols}
          onChange={(e) => setSymbols(e.target.value)}
        />
      </div>

      <div className="flex items-center gap-2">
        <Checkbox
          id="pipeline-dry-run"
          checked={dryRun}
          onCheckedChange={(checked) => setDryRun(checked)}
        />
        <Label htmlFor="pipeline-dry-run">Dry Run</Label>
      </div>

      <Button type="submit" disabled={mutation.isPending}>
        <Play data-icon="inline-start" />
        {mutation.isPending ? <span className="text-interactive">Running...</span> : 'Run Pipeline'}
      </Button>
    </form>
  );
}
