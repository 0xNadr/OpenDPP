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

export function RegulatorView({ dpp }: { dpp: DPPJsonLd }) {
  const {
    identification,
    composition,
    origin,
    manufacturing,
    compliance,
    authority,
    environmental,
    lifecycleGuidance,
  } = dpp;

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium text-muted-foreground">Regulator view</p>
        <h1 className="text-2xl font-semibold tracking-tight">
          {identification.productName}
        </h1>
        <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1 text-sm font-mono text-muted-foreground sm:grid-cols-3">
          <Field label="GTIN" value={identification.gtin} />
          <Field label="Lot" value={identification.lot} />
          <Field label="Serial" value={identification.serial} />
          <Field label="Brand" value={identification.brand} />
          <Field label="Model" value={identification.model} />
          <Field label="SKU" value={identification.sku} />
        </dl>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Economic operator</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-1">
          <p className="font-medium">{authority.economicOperator.name}</p>
          <p className="text-muted-foreground">{authority.economicOperator.country}</p>
          {authority.economicOperator.registrationNumber && (
            <p className="font-mono text-xs text-muted-foreground">
              {authority.economicOperator.registrationNumber}
            </p>
          )}
          {authority.economicOperator.address && (
            <p className="text-muted-foreground">{authority.economicOperator.address}</p>
          )}
          {authority.dataCarrier && (
            <p className="text-xs text-muted-foreground">
              Data carrier: <span className="font-mono">{authority.dataCarrier}</span>
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Certifications</CardTitle>
        </CardHeader>
        <CardContent>
          {compliance.certifications.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Scheme</TableHead>
                  <TableHead>Identifier</TableHead>
                  <TableHead>Issued</TableHead>
                  <TableHead>Valid until</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {compliance.certifications.map((c) => (
                  <TableRow key={`${c.scheme}-${c.identifier}`}>
                    <TableCell>{c.scheme}</TableCell>
                    <TableCell className="font-mono text-xs">{c.identifier}</TableCell>
                    <TableCell className="font-mono text-xs">{c.issuedOn ?? "—"}</TableCell>
                    <TableCell className="font-mono text-xs">{c.validUntil ?? "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-muted-foreground">None declared.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Supply chain</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>#</TableHead>
                <TableHead>Step</TableHead>
                <TableHead>Country</TableHead>
                <TableHead>Supplier</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="font-mono text-xs">0</TableCell>
                <TableCell>manufacturing</TableCell>
                <TableCell>{origin.countryOfManufacture}</TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {manufacturing.facilityId ?? "—"}
                </TableCell>
              </TableRow>
              {origin.supplyChain?.map((step, i) => (
                <TableRow key={`${step.step}-${i}`}>
                  <TableCell className="font-mono text-xs">{i + 1}</TableCell>
                  <TableCell>{step.step}</TableCell>
                  <TableCell>{step.country}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {step.supplierId ?? "anonymized"}
                    {step.attestationCredentialId ? (
                      <Badge variant="outline" className="ml-2">
                        VC: {step.attestationCredentialId.slice(0, 8)}…
                      </Badge>
                    ) : null}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Composition &amp; environmental</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <ul className="space-y-0.5">
            {composition.materials.map((m) => (
              <li key={m.name} className="flex justify-between">
                <span>{m.name}</span>
                <span className="font-mono text-muted-foreground">
                  {m.percentage}% (recycled {m.recycledContentPercentage ?? 0}%)
                </span>
              </li>
            ))}
          </ul>
          {environmental?.carbonFootprint && (
            <p className="text-muted-foreground">
              Carbon: {environmental.carbonFootprint.valueKgCO2e} kg CO₂e (
              {environmental.carbonFootprint.scope},{" "}
              {environmental.carbonFootprint.methodology ?? "method n/a"})
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Lifecycle guidance</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-2">
          <p>
            <span className="text-muted-foreground">End-of-life options: </span>
            {lifecycleGuidance.endOfLifeOptions.join(", ")}
          </p>
          {lifecycleGuidance.recyclabilityScore !== undefined && (
            <p>
              <span className="text-muted-foreground">Recyclability score: </span>
              <span className="font-mono">{lifecycleGuidance.recyclabilityScore}</span>
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Raw JSON-LD</CardTitle>
        </CardHeader>
        <CardContent>
          <details className="text-sm">
            <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
              Show / hide
            </summary>
            <pre className="mt-3 max-h-96 overflow-auto rounded-md bg-muted p-3 text-xs">
              {JSON.stringify(dpp, null, 2)}
            </pre>
          </details>
        </CardContent>
      </Card>
    </div>
  );
}

function Field({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return (
    <div className="flex gap-2">
      <dt className="font-sans text-xs uppercase tracking-wide">{label}</dt>
      <dd className="font-mono text-foreground">{value}</dd>
    </div>
  );
}
