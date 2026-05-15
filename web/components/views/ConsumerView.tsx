import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { MaterialBar } from "@/components/MaterialBar";
import { findCredentialFor, VerifiedBadge } from "@/components/VerifiedBadge";
import type { DPPJsonLd, VerifiableCredential } from "@/lib/api";

export function ConsumerView({
  dpp,
  credentials = [],
}: {
  dpp: DPPJsonLd;
  credentials?: VerifiableCredential[];
}) {
  const { identification, composition, origin, environmental, compliance, lifecycleGuidance } =
    dpp;

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium text-muted-foreground">{identification.brand}</p>
        <h1 className="text-3xl font-semibold tracking-tight">{identification.productName}</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Made in {origin.countryOfManufacture}
          {origin.countryOfFinalProcessing &&
          origin.countryOfFinalProcessing !== origin.countryOfManufacture
            ? `, finished in ${origin.countryOfFinalProcessing}`
            : ""}
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>What it's made of</CardTitle>
        </CardHeader>
        <CardContent>
          <MaterialBar materials={composition.materials} />
        </CardContent>
      </Card>

      {environmental?.carbonFootprint && (
        <Card>
          <CardHeader>
            <CardTitle>Environmental impact</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-baseline justify-between">
              <span className="text-muted-foreground">Carbon footprint</span>
              <span className="font-mono">
                {environmental.carbonFootprint.valueKgCO2e} kg CO₂e
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Scope: {environmental.carbonFootprint.scope}
              {environmental.carbonFootprint.methodology
                ? ` • Method: ${environmental.carbonFootprint.methodology}`
                : ""}
            </p>
            {environmental.waterUsageLiters !== undefined && (
              <>
                <Separator />
                <div className="flex items-baseline justify-between">
                  <span className="text-muted-foreground">Water usage</span>
                  <span className="font-mono">{environmental.waterUsageLiters} L</span>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {compliance.certifications.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Certifications</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {compliance.certifications.map((c) => {
                const vc = findCredentialFor(credentials, c.scheme, c.identifier);
                return (
                  <li
                    key={`${c.scheme}-${c.identifier}`}
                    className="flex flex-wrap items-center gap-2"
                  >
                    <Badge variant="secondary">{c.scheme}</Badge>
                    <code className="text-xs text-muted-foreground">{c.identifier}</code>
                    {vc && <VerifiedBadge vc={vc} />}
                  </li>
                );
              })}
            </ul>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Care &amp; lifecycle</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <div>
            <p className="font-medium">Care instructions</p>
            <ul className="mt-1 list-disc space-y-0.5 pl-5 text-muted-foreground">
              {lifecycleGuidance.careInstructions.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          </div>
          {lifecycleGuidance.repairGuidance && (
            <div>
              <p className="font-medium">Repair</p>
              <p className="mt-1 text-muted-foreground">{lifecycleGuidance.repairGuidance}</p>
            </div>
          )}
          <div>
            <p className="font-medium">End of life</p>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {lifecycleGuidance.endOfLifeOptions.map((opt) => (
                <Badge key={opt} variant="outline" className="capitalize">
                  {opt}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
