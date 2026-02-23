import { useState, useEffect } from "react";
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
import { toast } from "sonner";
import { UserPlus } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Employees({ user, onLogout }) {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);

  const [employeeForm, setEmployeeForm] = useState({
    name: "",
    email: "",
    joining_date: "",
    role: "employee",
    carry_forward_el: 0,
  });

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/employees`);
      setEmployees(response.data);
    } catch (error) {
      toast.error("Failed to load employees");
    } finally {
      setLoading(false);
    }
  };

  const handleAddEmployee = async (e) => {
    e.preventDefault();

    try {
      await axios.post(`${API}/employees`, employeeForm);
      toast.success("Employee added successfully!");
      setDialogOpen(false);
      setEmployeeForm({
        name: "",
        email: "",
        joining_date: "",
        role: "employee",
        carry_forward_el: 0,
      });
      fetchEmployees();
    } catch (error) {
      toast.error(
        error.response?.data?.detail || "Failed to add employee"
      );
    }
  };

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-slate-900">Employee Management</h1>
            <p className="text-slate-600 mt-2">Add and manage employees</p>
          </div>

          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button
                data-testid="add-employee-button"
                className="btn-pill bg-primary hover:bg-primary/90 text-white"
              >
                <UserPlus className="w-4 h-4 mr-2" />
                Add Employee
              </Button>
            </DialogTrigger>
            <DialogContent data-testid="add-employee-dialog">
              <DialogHeader>
                <DialogTitle>Add New Employee</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleAddEmployee} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    data-testid="employee-name-input"
                    value={employeeForm.name}
                    onChange={(e) =>
                      setEmployeeForm({ ...employeeForm, name: e.target.value })
                    }
                    required
                    className="bg-slate-50 focus:bg-white"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Work Email</Label>
                  <Input
                    id="email"
                    data-testid="employee-email-input"
                    type="email"
                    value={employeeForm.email}
                    onChange={(e) =>
                      setEmployeeForm({ ...employeeForm, email: e.target.value })
                    }
                    required
                    className="bg-slate-50 focus:bg-white"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="joining_date">Joining Date</Label>
                  <Input
                    id="joining_date"
                    data-testid="employee-joining-date-input"
                    type="date"
                    value={employeeForm.joining_date}
                    onChange={(e) =>
                      setEmployeeForm({
                        ...employeeForm,
                        joining_date: e.target.value,
                      })
                    }
                    required
                    className="bg-slate-50 focus:bg-white"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <Select
                    value={employeeForm.role}
                    onValueChange={(value) =>
                      setEmployeeForm({ ...employeeForm, role: value })
                    }
                  >
                    <SelectTrigger data-testid="employee-role-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="employee">Employee</SelectItem>
                      <SelectItem value="hr">HR</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="carry_forward_el">
                    Carry Forward Earned Leaves (Optional)
                  </Label>
                  <Input
                    id="carry_forward_el"
                    data-testid="employee-carry-forward-input"
                    type="number"
                    step="0.5"
                    min="0"
                    value={employeeForm.carry_forward_el}
                    onChange={(e) =>
                      setEmployeeForm({
                        ...employeeForm,
                        carry_forward_el: parseFloat(e.target.value) || 0,
                      })
                    }
                    className="bg-slate-50 focus:bg-white"
                  />
                </div>

                <Button
                  type="submit"
                  data-testid="submit-employee-button"
                  className="w-full btn-pill bg-primary hover:bg-primary/90 text-white"
                >
                  Add Employee
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Employees Table */}
        <Card className="p-6 border border-slate-200 shadow-sm bg-white rounded-xl">
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <div className="text-slate-600">Loading employees...</div>
            </div>
          ) : employees.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-slate-500">No employees added yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full" data-testid="employees-table">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">
                      Name
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">
                      Email
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">
                      Joining Date
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">
                      Role
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-700">
                      Carry Forward EL
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {employees.map((emp) => (
                    <tr
                      key={emp.employee_id}
                      data-testid={`employee-row-${emp.employee_id}`}
                      className="border-b border-slate-100 hover:bg-slate-50"
                    >
                      <td className="py-3 px-4 text-sm font-medium text-slate-900">
                        {emp.name}
                      </td>
                      <td className="py-3 px-4 text-sm text-slate-700">
                        {emp.email}
                      </td>
                      <td className="py-3 px-4 text-sm text-slate-700">
                        {emp.joining_date}
                      </td>
                      <td className="py-3 px-4 text-sm">
                        <span
                          className={`badge ${
                            emp.role === "hr" ? "badge-wfh" : "badge-ooo"
                          }`}
                        >
                          {emp.role === "hr" ? "HR" : "Employee"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-slate-700">
                        {emp.carry_forward_el || 0}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
}
