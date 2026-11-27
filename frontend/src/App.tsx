import { useState, useEffect } from 'react'
import './App.css'

const API = 'http://localhost:8000/api'

type Snapshot = { id: number; taken_at: string; tool_count: number; schema_hash: string; token_estimate: number }
type TestRun = { id: number; run_at: string; scenario: string; verdict: string; explanation: string }

function App() {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([])
  const [runs, setRuns] = useState<TestRun[]>([])
  const [selected, setSelected] = useState<number | null>(null)
  const [diff, setDiff] = useState<any>(null)
  const [report, setReport] = useState<any>(null)
  const [status, setStatus] = useState('Ready')

  const refresh = async () => {
    const s = await fetch(`${API}/snapshots`).then(r => r.json())
    const t = await fetch(`${API}/test-runs`).then(r => r.json())
    const rep = await fetch(`${API}/report`).then(r => r.json())
    setSnapshots(s)
    setRuns(t)
    setReport(rep)
  }

  useEffect(() => { refresh() }, [])

  const takeSnapshot = async () => {
    setStatus('Taking snapshot...')
    await fetch(`${API}/snapshots`, { method: 'POST' })
    await refresh()
    setStatus('Snapshot saved')
  }

  const runScenario = async (sc: string) => {
    setStatus(`Running scenario ${sc}...`)
    const res = await fetch(`${API}/scenarios/${sc}`, { method: 'POST' }).then(r => r.json())
    await refresh()
    setStatus(`${sc}: ${res.verdict} — ${res.explanation}`)
  }

  const loadDiff = async (id1: number, id2: number) => {
    const d = await fetch(`${API}/diff/${id1}/${id2}`).then(r => r.json())
    setDiff(d)
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <header className="mb-8 border-b border-slate-800 pb-4">
        <h1 className="text-3xl font-bold">MCP Schema Contract & Silent-Failure Studio</h1>
        <p className="text-slate-400 mt-1">Local-first interactive reliability application • Bundled synthetic MCP server</p>
        <p className="text-xs text-amber-400 mt-1">Token estimates are approximate (character-based). All results are from live MCP protocol calls.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Controls */}
        <div className="space-y-4">
          <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <h2 className="font-semibold mb-3">Server Inventory</h2>
            <button onClick={takeSnapshot} className="w-full bg-emerald-600 hover:bg-emerald-500 py-2 rounded-lg font-medium">
              Connect & Take Snapshot
            </button>
            <p className="text-xs text-slate-500 mt-2">{status}</p>
          </div>

          <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <h2 className="font-semibold mb-3">Contract & Outcome Tests</h2>
            <div className="grid grid-cols-2 gap-2">
              {['A','B','C','D','E','F'].map(sc => (
                <button key={sc} onClick={() => runScenario(sc)} className="bg-slate-800 hover:bg-slate-700 py-2 rounded text-sm">
                  Scenario {sc}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <h2 className="font-semibold mb-2">Reliability Report</h2>
            {report && (
              <pre className="text-xs bg-slate-950 p-2 rounded overflow-auto">{JSON.stringify(report, null, 2)}</pre>
            )}
            <button onClick={() => navigator.clipboard.writeText(JSON.stringify(report, null, 2))} className="mt-2 text-xs text-sky-400">
              Copy JSON
            </button>
          </div>
        </div>

        {/* Middle: Snapshots */}
        <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <h2 className="font-semibold mb-3">Schema Snapshot History</h2>
          <div className="space-y-2 max-h-96 overflow-auto">
            {snapshots.map(s => (
              <div key={s.id} onClick={() => setSelected(s.id)} className={`p-3 rounded-lg cursor-pointer border ${selected===s.id ? 'border-emerald-500 bg-slate-800' : 'border-slate-800 hover:bg-slate-800'}`}>
                <div className="flex justify-between text-sm">
                  <span>#{s.id} • {s.tool_count} tools</span>
                  <span className="text-slate-400">{s.token_estimate} tok est.</span>
                </div>
                <div className="text-xs text-slate-500 font-mono">{s.schema_hash}</div>
                <div className="text-xs text-slate-600">{s.taken_at}</div>
              </div>
            ))}
          </div>
          {snapshots.length >= 2 && (
            <button onClick={() => loadDiff(snapshots[1].id, snapshots[0].id)} className="mt-3 w-full bg-sky-700 py-2 rounded text-sm">
              Diff Latest Two Snapshots
            </button>
          )}
        </div>

        {/* Right: Diff + Runs */}
        <div className="space-y-4">
          <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <h2 className="font-semibold mb-2">Visual Schema Comparison</h2>
            {diff ? (
              <div>
                <p className="text-sm mb-2">Breaking changes: <span className="text-red-400 font-bold">{diff.breaking_count}</span></p>
                <ul className="text-xs space-y-1 max-h-48 overflow-auto">
                  {diff.changes.map((c: any, i: number) => (
                    <li key={i} className={c.breaking ? 'text-red-300' : 'text-slate-300'}>
                      {c.tool}: {c.type} {c.breaking ? '(BREAKING)' : ''}
                    </li>
                  ))}
                </ul>
              </div>
            ) : <p className="text-slate-500 text-sm">Select two snapshots to compare</p>}
          </div>

          <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <h2 className="font-semibold mb-2">Test Execution History</h2>
            <div className="space-y-2 max-h-64 overflow-auto text-sm">
              {runs.map(r => (
                <div key={r.id} className="p-2 bg-slate-950 rounded border border-slate-800">
                  <div className="flex justify-between">
                    <span>Scenario {r.scenario}</span>
                    <span className={r.verdict==='PASS' ? 'text-emerald-400' : r.verdict==='FAIL' ? 'text-red-400' : 'text-amber-400'}>
                      {r.verdict}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{r.explanation}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
