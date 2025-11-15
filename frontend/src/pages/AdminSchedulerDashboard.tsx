import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

interface SchedulerDashboardData {
  summary: {
    [key: string]: number;
    success: number;
    failed: number;
    partial: number;
    running: number;
    success_rate: number;
    total_active_schedules: number;
    total_schedules: number;
  };
  recent_activity: TaskHistoryItem[];
  active_schedules: ScheduleItem[];
  all_schedules: ScheduleItem[];
  health: {
    failed_tasks: TaskHistoryItem[];
    overdue_tasks: ScheduleItem[];
    stalled_tasks: TaskHistoryItem[];
    has_issues: boolean;
  };
}

interface TaskHistoryItem {
  id: number;
  scheduled_task_id: number;
  status: string;
  user_email: string | null;
  user_name: string | null;
  brand_name: string | null;
  brand_id: number;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  collection_responses: number | null;
  analysis_responses: number | null;
  error_message: string | null;
  schedule_type: string | null;
}

interface ScheduleItem {
  id: number;
  user_email: string | null;
  user_name: string | null;
  user_id: number;
  brand_name: string | null;
  brand_id: number;
  schedule_type: string;
  is_enabled: boolean;
  next_run_at: string | null;
  last_run_at: string | null;
  last_status: string | null;
  send_email_notification: boolean;
  notification_email: string | null;
  timezone: string;
  is_overdue: boolean;
}

export default function AdminSchedulerDashboard() {
  const [dashboardData, setDashboardData] = useState<SchedulerDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);
  const [activeTab, setActiveTab] = useState<'overview' | 'activity' | 'schedules' | 'health'>('overview');

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/admin/scheduler/dashboard?days=${days}`);
      setDashboardData(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [days]);

  const getStatusBadge = (status: string) => {
    const statusColors: { [key: string]: string } = {
      success: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      partial: 'bg-yellow-100 text-yellow-800',
      running: 'bg-blue-100 text-blue-800',
    };
    return statusColors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  if (!dashboardData) return null;

  const summaryKeys = Object.keys(dashboardData.summary);
  const totalRunsKey = summaryKeys.find(k => k.startsWith('total_runs_last')) || 'total_runs';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Scheduler Dashboard</h1>
        <div className="flex items-center gap-4">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="border border-gray-300 rounded-md px-3 py-2"
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <button
            onClick={fetchDashboard}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Health Alert */}
      {dashboardData.health.has_issues && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Issues Detected</h3>
              <div className="mt-2 text-sm text-red-700">
                <ul className="list-disc pl-5 space-y-1">
                  {dashboardData.health.failed_tasks.length > 0 && (
                    <li>{dashboardData.health.failed_tasks.length} failed/partial task(s)</li>
                  )}
                  {dashboardData.health.overdue_tasks.length > 0 && (
                    <li>{dashboardData.health.overdue_tasks.length} overdue schedule(s)</li>
                  )}
                  {dashboardData.health.stalled_tasks.length > 0 && (
                    <li>{dashboardData.health.stalled_tasks.length} stalled task(s)</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Total Runs</div>
          <div className="mt-2 text-3xl font-semibold text-gray-900">
            {dashboardData.summary[totalRunsKey]}
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Success Rate</div>
          <div className="mt-2 text-3xl font-semibold text-green-600">
            {dashboardData.summary.success_rate}%
          </div>
          <div className="mt-1 text-sm text-gray-500">
            {dashboardData.summary.success} successful
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Active Schedules</div>
          <div className="mt-2 text-3xl font-semibold text-blue-600">
            {dashboardData.summary.total_active_schedules}
          </div>
          <div className="mt-1 text-sm text-gray-500">
            of {dashboardData.summary.total_schedules} total
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm font-medium text-gray-500">Failed/Issues</div>
          <div className="mt-2 text-3xl font-semibold text-red-600">
            {dashboardData.summary.failed + dashboardData.summary.partial}
          </div>
          <div className="mt-1 text-sm text-gray-500">
            {dashboardData.summary.failed} failed, {dashboardData.summary.partial} partial
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {(['overview', 'activity', 'schedules', 'health'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`
                whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white shadow rounded-lg p-6">
        {activeTab === 'overview' && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Overview</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="font-medium mb-2">Status Breakdown</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Success:</span>
                    <span className="font-semibold text-green-600">{dashboardData.summary.success}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Failed:</span>
                    <span className="font-semibold text-red-600">{dashboardData.summary.failed}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Partial:</span>
                    <span className="font-semibold text-yellow-600">{dashboardData.summary.partial}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Running:</span>
                    <span className="font-semibold text-blue-600">{dashboardData.summary.running}</span>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="font-medium mb-2">Active Schedules</h3>
                <div className="text-sm text-gray-600">
                  {dashboardData.active_schedules.length === 0 ? (
                    <p>No active schedules</p>
                  ) : (
                    <ul className="space-y-1">
                      {dashboardData.active_schedules.slice(0, 5).map((schedule) => (
                        <li key={schedule.id}>
                          {schedule.user_email} - {schedule.brand_name}
                        </li>
                      ))}
                      {dashboardData.active_schedules.length > 5 && (
                        <li className="text-gray-500">
                          ... and {dashboardData.active_schedules.length - 5} more
                        </li>
                      )}
                    </ul>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'activity' && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Recent Activity</h2>
            {dashboardData.recent_activity.length === 0 ? (
              <p className="text-gray-500">No recent activity</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Brand</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Started</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Collected</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Analyzed</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {dashboardData.recent_activity.map((item) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(item.status)}`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {item.user_email || 'Unknown'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {item.brand_name || 'Unknown'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(item.started_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDuration(item.duration_seconds)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {item.collection_responses || 0}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {item.analysis_responses || 0}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === 'schedules' && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">All Schedules</h2>
            {dashboardData.all_schedules.length === 0 ? (
              <p className="text-gray-500">No schedules configured</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Brand</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Next Run</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Run</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {dashboardData.all_schedules.map((schedule) => (
                      <tr key={schedule.id} className={schedule.is_overdue ? 'bg-red-50' : 'hover:bg-gray-50'}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            schedule.is_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {schedule.is_enabled ? 'Active' : 'Disabled'}
                          </span>
                          {schedule.is_overdue && (
                            <span className="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                              Overdue
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {schedule.user_email || 'Unknown'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {schedule.brand_name || 'Unknown'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {schedule.schedule_type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(schedule.next_run_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(schedule.last_run_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {schedule.last_status && (
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(schedule.last_status)}`}>
                              {schedule.last_status}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === 'health' && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold">Health Monitoring</h2>

            {/* Failed Tasks */}
            <div>
              <h3 className="text-lg font-semibold text-red-600 mb-2">
                Failed/Partial Tasks ({dashboardData.health.failed_tasks.length})
              </h3>
              {dashboardData.health.failed_tasks.length === 0 ? (
                <p className="text-gray-500">No failed tasks</p>
              ) : (
                <div className="space-y-2">
                  {dashboardData.health.failed_tasks.map((task) => (
                    <div key={task.id} className="border border-red-200 rounded p-3 bg-red-50">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium">{task.user_email} - {task.brand_name}</div>
                          <div className="text-sm text-gray-600">{formatDateTime(task.started_at)}</div>
                          {task.error_message && (
                            <div className="text-sm text-red-600 mt-1">{task.error_message}</div>
                          )}
                        </div>
                        <span className={`px-2 py-1 text-xs font-semibold rounded ${getStatusBadge(task.status)}`}>
                          {task.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Overdue Tasks */}
            <div>
              <h3 className="text-lg font-semibold text-orange-600 mb-2">
                Overdue Schedules ({dashboardData.health.overdue_tasks.length})
              </h3>
              {dashboardData.health.overdue_tasks.length === 0 ? (
                <p className="text-gray-500">No overdue schedules</p>
              ) : (
                <div className="space-y-2">
                  {dashboardData.health.overdue_tasks.map((schedule) => (
                    <div key={schedule.id} className="border border-orange-200 rounded p-3 bg-orange-50">
                      <div className="font-medium">{schedule.user_email} - {schedule.brand_name}</div>
                      <div className="text-sm text-gray-600">
                        Should have run: {formatDateTime(schedule.next_run_at)}
                      </div>
                      <div className="text-sm text-gray-600">
                        Last run: {formatDateTime(schedule.last_run_at)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Stalled Tasks */}
            <div>
              <h3 className="text-lg font-semibold text-yellow-600 mb-2">
                Stalled Tasks (Running &gt; 2 hours) ({dashboardData.health.stalled_tasks.length})
              </h3>
              {dashboardData.health.stalled_tasks.length === 0 ? (
                <p className="text-gray-500">No stalled tasks</p>
              ) : (
                <div className="space-y-2">
                  {dashboardData.health.stalled_tasks.map((task) => (
                    <div key={task.id} className="border border-yellow-200 rounded p-3 bg-yellow-50">
                      <div className="font-medium">{task.user_email} - {task.brand_name}</div>
                      <div className="text-sm text-gray-600">
                        Started: {formatDateTime(task.started_at)}
                      </div>
                      <div className="text-sm text-gray-600">
                        Collected: {task.collection_responses || 0}, Analyzed: {task.analysis_responses || 0}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
