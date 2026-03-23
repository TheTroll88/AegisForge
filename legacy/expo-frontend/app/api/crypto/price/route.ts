// app/api/crypto/price/route.ts
export async function GET() {
  return Response.json({ price: 30500.52, currency: 'BTC' });
}
