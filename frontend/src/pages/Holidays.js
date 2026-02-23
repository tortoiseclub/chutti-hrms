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
import { toast } from "sonner";
import { CalendarPlus, Trash2 } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Holidays({ user, onLogout }) {
  const [holidays, setHolidays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  const [holidayForm, setHolidayForm] = useState({
    date: "",
    name: "",
    year: new Date().getFullYear(),
  });

  useEffect(() => {
    fetchHolidays();
  }, [selectedYear]);

  const fetchHolidays = async () => {
    try {
      const response = await axios.get(`${API}/holidays?year=${selectedYear}`);
      setHolidays(response.data.sort((a, b) => a.date.localeCompare(b.date)));
    } catch (error) {
      toast.error("Failed to load holidays");
    } finally {
      setLoading(false);
    }
  };

  const handleAddHoliday = async (e) => {
    e.preventDefault();

    // Extract year from date
    const year = new Date(holidayForm.date).getFullYear();

    try {
      await axios.post(`${API}/holidays`, {
        ...holidayForm,
        year,
      });
      toast.success("Holiday added successfully!");
      setDialogOpen(false);
      setHolidayForm({
        date: "",
        name: "",
        year: new Date().getFullYear(),
      });
      fetchHolidays();
    } catch (error) {
      toast.error("Failed to add holiday");
    }
  };

  const handleDeleteHoliday = async (holidayId) => {
    if (!window.confirm("Are you sure you want to delete this holiday?")) {
      return;
    }

    try {
      await axios.delete(`${API}/holidays/${holidayId}`);
      toast.success("Holiday deleted successfully");
      fetchHolidays();
    } catch (error) {
      toast.error("Failed to delete holiday");
    }
  };

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-slate-900">Holiday Management</h1>
            <p className="text-slate-600 mt-2">Manage national and company holidays</p>
          </div>

          <div className="flex gap-4 items-center">
            <Input
              data-testid="year-filter-input"
              type="number"
              min="2020"
              max="2030"
              value={selectedYear}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              className="w-32 bg-slate-50 focus:bg-white"
            />

            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  data-testid="add-holiday-button"
                  className="btn-pill bg-primary hover:bg-primary/90 text-white"
                >
                  <CalendarPlus className="w-4 h-4 mr-2" />
                  Add Holiday
                </Button>
              </DialogTrigger>
              <DialogContent data-testid="add-holiday-dialog">
                <DialogHeader>
                  <DialogTitle>Add New Holiday</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleAddHoliday} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Holiday Name</Label>
                    <Input
                      id="name"
                      data-testid="holiday-name-input"
                      value={holidayForm.name}
                      onChange={(e) =>
                        setHolidayForm({ ...holidayForm, name: e.target.value })
                      }
                      required
                      placeholder="e.g., Diwali, Christmas"
                      className="bg-slate-50 focus:bg-white"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="date">Date</Label>
                    <Input
                      id="date"
                      data-testid="holiday-date-input"
                      type="date"
                      value={holidayForm.date}
                      onChange={(e) =>
                        setHolidayForm({ ...holidayForm, date: e.target.value })
                      }
                      required
                      className="bg-slate-50 focus:bg-white"
                    />
                  </div>

                  <Button
                    type="submit"
                    data-testid="submit-holiday-button"
                    className="w-full btn-pill bg-primary hover:bg-primary/90 text-white"
                  >
                    Add Holiday
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Holidays List */}
        <Card className="p-6 border border-slate-200 shadow-sm bg-white rounded-xl">
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <div className="text-slate-600">Loading holidays...</div>
            </div>
          ) : holidays.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-slate-500">No holidays added for {selectedYear}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {holidays.map((holiday) => (
                <div
                  key={holiday.holiday_id}
                  data-testid={`holiday-item-${holiday.holiday_id}`}
                  className="flex items-center justify-between p-4 rounded-lg leave-holiday card-hover"
                >
                  <div>
                    <p className="font-medium text-slate-900">{holiday.name}</p>
                    <p className="text-sm mt-1 opacity-75">
                      {new Date(holiday.date).toLocaleDateString("en-US", {
                        weekday: "long",
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })}
                    </p>
                  </div>
                  <Button
                    data-testid={`delete-holiday-${holiday.holiday_id}`}
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDeleteHoliday(holiday.holiday_id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
}
