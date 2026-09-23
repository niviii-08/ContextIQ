import { EnhancedContextIntelligence } from "@/components/analytics/enhanced-context-intelligence";

export default function ContextPage() {
  // In a real app, this would come from authentication
  const userId = "user-123";
  
  return <EnhancedContextIntelligence userId={userId} periodDays={30} />;
}
