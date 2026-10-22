import { EnhancedDashboard } from "@/components/dashboard/enhanced-dashboard";

export default function DashboardPage() {
  const userId =
    process.env.NEXT_PUBLIC_DEV_USER_ID ?? "11111111-1111-1111-1111-111111111111"; 
  
  return (
    <div className="space-y-6">
      <EnhancedDashboard userId={userId} periodDays={30} />
    </div>
  );
}
