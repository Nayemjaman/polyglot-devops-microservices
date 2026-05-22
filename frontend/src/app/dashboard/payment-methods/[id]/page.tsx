import { PaymentMethodDetailsScreen } from "@/components/dashboard/payment-method-details";

export default async function PaymentMethodDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <PaymentMethodDetailsScreen id={id} />;
}
