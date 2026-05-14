import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { DPPJsonLd } from "@/lib/api";

export function RecyclerView({ dpp }: { dpp: DPPJsonLd }) {
  const { identification, composition, compliance, lifecycleGuidance, environmental } = dpp;

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium text-muted-foreground">Recycler view</p>
        <h1 className="text-2xl font-semibold tracking-tight">
          {identification.productName}
        </h1>
        <p className="mt-1 text-sm font-mono text-muted-foreground">
          GTIN {identification.gtin}
          {identification.lot ? ` · Lot ${identification.lot}` : ""}
          {identification.serial ? ` · Serial ${identification.serial}` : ""}
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Material composition</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Material</TableHead>
                <TableHead className="text-right">% by weight</TableHead>
                <TableHead className="text-right">Recycled</TableHead>
                <TableHead className="text-right">Bio-based</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {composition.materials.map((m) => (
                <TableRow key={m.name}>
                  <TableCell>{m.name}</TableCell>
                  <TableCell className="text-right font-mono">{m.percentage}%</TableCell>
                  <TableCell className="text-right font-mono">
                    {m.recycledContentPercentage ?? 0}%
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {m.biobasedContentPercentage ?? 0}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {composition.recycledContentOverallPercentage !== undefined && (
            <p className="mt-3 text-xs text-muted-foreground">
              Overall recycled content: {composition.recycledContentOverallPercentage}%
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>End-of-life pathways</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex flex-wrap gap-1.5">
            {lifecycleGuidance.endOfLifeOptions.map((opt, i) => (
              <Badge
                key={opt}
                variant={i === 0 ? "default" : "outline"}
                className="capitalize"
              >
                {i === 0 ? "Preferred: " : ""}
                {opt}
              </Badge>
            ))}
          </div>
          {lifecycleGuidance.recyclabilityScore !== undefined && (
            <p className="text-muted-foreground">
              Recyclability score:{" "}
              <span className="font-mono text-foreground">
                {(lifecycleGuidance.recyclabilityScore * 100).toFixed(0)}/100
              </span>
            </p>
          )}
          {lifecycleGuidance.repairGuidance && (
            <p className="text-muted-foreground">{lifecycleGuidance.repairGuidance}</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Substances of concern</CardTitle>
        </CardHeader>
        <CardContent>
          {compliance.substancesOfConcern && compliance.substancesOfConcern.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Substance</TableHead>
                  <TableHead>CAS</TableHead>
                  <TableHead className="text-right">ppm</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {compliance.substancesOfConcern.map((s) => (
                  <TableRow key={s.name}>
                    <TableCell>{s.name}</TableCell>
                    <TableCell className="font-mono">{s.casNumber ?? "—"}</TableCell>
                    <TableCell className="text-right font-mono">
                      {s.concentrationPpm ?? "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-muted-foreground">None declared.</p>
          )}
        </CardContent>
      </Card>

      {environmental?.carbonFootprint && (
        <Card>
          <CardHeader>
            <CardTitle>Environmental impact</CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-1">
            <p>
              <span className="text-muted-foreground">Carbon: </span>
              <span className="font-mono">
                {environmental.carbonFootprint.valueKgCO2e} kg CO₂e (
                {environmental.carbonFootprint.scope})
              </span>
            </p>
            {environmental.waterUsageLiters !== undefined && (
              <p>
                <span className="text-muted-foreground">Water: </span>
                <span className="font-mono">{environmental.waterUsageLiters} L</span>
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
