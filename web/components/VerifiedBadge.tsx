import { Badge } from "@/components/ui/badge";
import type { VerifiableCredential } from "@/lib/api";

export function VerifiedBadge({ vc }: { vc: VerifiableCredential }) {
  return (
    <Badge
      variant="default"
      title={`Signed by ${vc.supplier.name} (${vc.supplier.did})`}
      className="gap-1 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-700 dark:hover:bg-emerald-800"
    >
      <span aria-hidden>✓</span>
      <span>Verified by {vc.supplier.name}</span>
    </Badge>
  );
}

export function findCredentialFor(
  credentials: VerifiableCredential[] | undefined,
  scheme: string | undefined,
  identifier: string | undefined,
): VerifiableCredential | undefined {
  if (!credentials || !scheme) return undefined;
  return credentials.find(
    (c) =>
      c.body.credentialSubject.certificationScheme === scheme &&
      (!identifier ||
        c.body.credentialSubject.certificationId === identifier),
  );
}
