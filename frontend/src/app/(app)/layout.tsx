import { Nav } from "@/components/nav";
import { requireUser } from "@/lib/dal";

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await requireUser();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <Nav
        isAdmin={user.is_admin}
        fullName={user.full_name}
        role={user.role}
        organizationName={user.organization?.name}
      />
      <main className="mx-auto max-w-7xl px-4 pb-10 pt-20 sm:px-6 md:pl-80 md:pr-8 md:pt-8 lg:pr-10">
        {children}
      </main>
    </div>
  );
}
