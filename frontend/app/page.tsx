import { EnhancedDashboard } from "@/components/dashboard/enhanced-dashboard";

export default function DashboardPage() {
  // In a real app, this would come from authentication
  const userId = "user-123"; 
  
  return (
    <div className="space-y-6">
      <EnhancedDashboard userId={userId} periodDays={30} />
    </div>
  );
}
