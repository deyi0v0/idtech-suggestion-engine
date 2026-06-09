export default function Dashboard() {
  return (
    <div className='text-primary p-10'>
      <h1 className='text-2xl font-bold mb-4'>Admin Dashboard</h1>
      <nav>
        <ul className='space-y-2'>
          <li><a href='/admin/leads' className='underline text-blue-500 hover:text-blue-700'>Manage Leads</a></li>
          <li><a href='/admin/hardware' className='underline text-blue-500 hover:text-blue-700'>Manage Hardware</a></li>
          <li><a href='/admin/software' className='underline text-blue-500 hover:text-blue-700'>Manage Software</a></li>
          <li><a href='/admin/prompts' className='underline text-blue-500 hover:text-blue-700'>Manage Prompts</a></li>
          <li><a href='/admin/docs' className='underline text-blue-500 hover:text-blue-700'>Manage Docs</a></li>
        </ul>
      </nav>
    </div>
  );
}