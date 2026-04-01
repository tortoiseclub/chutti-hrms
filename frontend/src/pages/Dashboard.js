import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import Layout from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Calendar, Clock, TrendingUp, Users } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard({ user, onLogout }) {
  const [balance, setBalance] = useState(null);
  const [allBalances, setAllBalances] = useState([]);
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Leave form state
  const [leaveForm, setLeaveForm] = useState({
    start_date: "",
    end_date: "",
    leave_type: "ooo",
    reason: "",
  });

  const fetchData = useCallback(async () => {
    try {
      const [balanceRes, allBalancesRes, leavesRes] = await Promise.all([
        axios.get(`${API}/employees/${user.employee_id}/balance`),
        axios.get(`${API}/balances`, {
          headers: {
            'X-Employee-Id': user.employee_id,
            'X-Employee-Role': user.role
          }
        }),
        axios.get(`${API}/leaves?year=${new Date().getFullYear()}`),
      ]);

      setBalance(balanceRes.data);
      setAllBalances(allBalancesRes.data);
      setLeaves(leavesRes.data);
    } catch (error) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [user.employee_id, user.role]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleApplyLeave = async (e) => {
    e.preventDefault();

    try {
      await axios.post(`${API}/leaves`, {
        employee_id: user.employee_id,
        ...leaveForm,
      });

      toast.success("Leave applied successfully!");
      setDialogOpen(false);
      setLeaveForm({
        start_date: "",
        end_date: "",
        leave_type: "ooo",
        reason: "",
      });
      fetchData();
    } catch (error) {
      toast.error(
        error.response?.data?.detail || "Failed to apply leave"
      );
    }
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-96">
          <div className="text-slate-600">Loading...</div>
        </div>
      </Layout>
    );
  }

  const myLeaves = leaves.filter((l) => l.employee_id === user.employee_id);

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-slate-900">
              Welcome, {user.name}
            </h1>
            <p className="text-slate-600 mt-2">Manage your leaves and view team availability</p>
          </div>

          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button
                data-testid="apply-leave-button"
                className="btn-pill bg-primary hover:bg-primary/90 text-white"
              >
                Apply for Leave
              </Button>
            </DialogTrigger>
            <DialogContent data-testid="apply-leave-dialog">
              <DialogHeader>
                <DialogTitle>Apply for Leave</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleApplyLeave} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="leave_type">Leave Type</Label>
                  <Select
                    value={leaveForm.leave_type}
                    onValueChange={(value) =>
                      setLeaveForm({ ...leaveForm, leave_type: value })
                    }
                  >
                    <SelectTrigger data-testid="leave-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ooo">Out of Office (OOO)</SelectItem>
                      <SelectItem value="wfh">Work From Home (WFH)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="start_date">Start Date</Label>
                  <Input
                    id="start_date"
                    data-testid="leave-start-date-input"
                    type="date"
                    value={leaveForm.start_date}
                    onChange={(e) =>
                      setLeaveForm({ ...leaveForm, start_date: e.target.value })
                    }
                    required
                    className="bg-slate-50 focus:bg-white"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="end_date">End Date</Label>
                  <Input
                    id="end_date"
                    data-testid="leave-end-date-input"
                    type="date"
                    value={leaveForm.end_date}
                    onChange={(e) =>
                      setLeaveForm({ ...leaveForm, end_date: e.target.value })
                    }
                    required
                    className="bg-slate-50 focus:bg-white"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reason">Reason (Optional)</Label>
                  <Textarea
                    id="reason"
                    data-testid="leave-reason-input"
                    value={leaveForm.reason}
                    onChange={(e) =>
                      setLeaveForm({ ...leaveForm, reason: e.target.value })
                    }
                    className="bg-slate-50 focus:bg-white"
                    rows={3}
                  />
                </div>

                <Button
                  type="submit"
                  data-testid="submit-leave-button"
                  className="w-full btn-pill bg-primary hover:bg-primary/90 text-white"
                >
                  Submit Leave Request
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats Grid - Bento Layout */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Earned Leave */}
          <Card
            data-testid="earned-leave-card"
            className="p-6 card-hover border border-slate-200 shadow-sm bg-white rounded-xl"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-600 font-medium">Earned Leave</p>
                <p className="text-3xl font-bold text-slate-900 mt-2">
                  {balance?.earned_leave.available || 0}
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  of {balance?.earned_leave.total || 0} available
                </p>
              </div>
              <div className="bg-teal-50 p-3 rounded-full">
                <TrendingUp className="w-6 h-6 text-primary" />
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-100">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Used:</span>
                <span className="font-medium text-slate-900">
                  {balance?.earned_leave.used || 0}
                </span>
              </div>
            </div>
          </Card>

          {/* Casual Leave */}
          <Card
            data-testid="casual-leave-card"
            className="p-6 card-hover border border-slate-200 shadow-sm bg-white rounded-xl"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-600 font-medium">Casual Leave</p>
                <p className="text-3xl font-bold text-slate-900 mt-2">
                  {balance?.casual_leave.available || 0}
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  of {balance?.casual_leave.total || 0} available
                </p>
              </div>
              <div className="bg-blue-50 p-3 rounded-full">
                <Clock className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-100">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Used:</span>
                <span className="font-medium text-slate-900">
                  {balance?.casual_leave.used || 0}
                </span>
              </div>
            </div>
          </Card>

          {/* WFH */}
          <Card
            data-testid="wfh-card"
            className="p-6 card-hover border border-slate-200 shadow-sm bg-white rounded-xl"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-600 font-medium">Work From Home</p>
                <p className="text-3xl font-bold text-slate-900 mt-2">
                  {balance?.wfh.available || 0}
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  of {balance?.wfh.total || 0} available
                </p>
              </div>
              <div className="bg-amber-50 p-3 rounded-full">
                <Users className="w-6 h-6 text-amber-600" />
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-100">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Used:</span>
                <span className="font-medium text-slate-900">
                  {balance?.wfh.used || 0}
                </span>
              </div>
            </div>
          </Card>
        </div>

        {/* My Recent Leaves */}
        <Card className="p-6 border border-slate-200 shadow-sm bg-white rounded-xl">
          <h2 className="text-xl font-bold text-slate-900 mb-4">My Recent Leaves</h2>
          {myLeaves.length === 0 ? (
            <p className="text-slate-500 text-center py-8">No leaves applied yet</p>
          ) : (
            <div className="space-y-3">
              {myLeaves.slice(0, 5).map((leave) => (
                <div
                  key={leave.leave_id}
                  data-testid={`leave-item-${leave.leave_id}`}
                  className={`p-4 rounded-lg ${
                    leave.leave_type === "ooo" ? "leave-ooo" : "leave-wfh"
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">
                        {leave.leave_type === "ooo" ? "Out of Office" : "Work From Home"}
                      </p>
                      <p className="text-sm mt-1">
                        {leave.start_date} to {leave.end_date} ({leave.days} days)
                      </p>
                      {leave.reason && (
                        <p className="text-sm mt-2 opacity-75">{leave.reason}</p>
                      )}
                    </div>
                    <span
                      className={`badge ${
                        leave.leave_type === "ooo" ? "badge-ooo" : "badge-wfh"
                      }`}
                    >
                      {leave.days} days
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Team Leave Balances - Only visible to HR */}
        {user.role === "hr" && (
          <Card className="p-6 border border-slate-200 shadow-sm bg-white rounded-xl">
            <h2 className="text-xl font-bold text-slate-900 mb-4">Team Leave Balances</h2>
            <div className="overflow-x-auto">
              <table className="w-full" data-testid="team-balances-table">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">
                      Employee
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">
                      Earned Leave
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">
                      Casual Leave
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">
                      WFH
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {allBalances.map((bal) => (
                    <tr
                      key={bal.employee_id}
                      data-testid={`balance-row-${bal.employee_id}`}
                      className="border-b border-slate-100 hover:bg-slate-50"
                    >
                      <td className="py-3 px-4 text-sm font-medium text-slate-900">
                        {bal.employee_name}
                      </td>
                      <td className="py-3 px-4 text-sm text-slate-700">
                        {bal.earned_leave.available} / {bal.earned_leave.total}
                      </td>
                      <td className="py-3 px-4 text-sm text-slate-700">
                        {bal.casual_leave.available} / {bal.casual_leave.total}
                      </td>
                      <td className="py-3 px-4 text-sm text-slate-700">
                        {bal.wfh.available} / {bal.wfh.total}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </Layout>
  );
}
