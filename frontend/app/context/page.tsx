import { EnhancedContextIntelligence } from "@/components/analytics/enhanced-context-intelligence";

export default function ContextPage() {
  const userId =
    process.env.NEXT_PUBLIC_DEV_USER_ID ?? "11111111-1111-1111-1111-111111111111";
  
  return <EnhancedContextIntelligence userId={userId} periodDays={30} />;
}
