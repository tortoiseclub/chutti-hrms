import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { ChevronLeft, ChevronRight } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

export default function Calendar({ user, onLogout }) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchCalendarData = useCallback(async () => {
    try {
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth() + 1;

      const response = await axios.get(
        `${API}/calendar?year=${year}&month=${month}`
      );
      setEvents(response.data.events);
    } catch (error) {
      toast.error("Failed to load calendar");
    } finally {
      setLoading(false);
    }
  }, [currentDate]);

  useEffect(() => {
    fetchCalendarData();
  }, [fetchCalendarData]);

  const handleDeleteLeave = async (leaveId) => {
    if (!window.confirm("Are you sure you want to remove this leave?")) {
      return;
    }

    try {
      await axios.delete(`${API}/leaves/${leaveId}`);
      toast.success("Leave removed successfully");
      fetchCalendarData();
    } catch (error) {
      toast.error("Failed to remove leave");
    }
  };

  const getDaysInMonth = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    return new Date(year, month, 1).getDay();
  };

  const previousMonth = () => {
    setCurrentDate(
      new Date(currentDate.getFullYear(), currentDate.getMonth() - 1)
    );
  };

  const nextMonth = () => {
    setCurrentDate(
      new Date(currentDate.getFullYear(), currentDate.getMonth() + 1)
    );
  };

  const getEventsForDate = (day) => {
    const dateStr = `${currentDate.getFullYear()}-${String(
      currentDate.getMonth() + 1
    ).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    return events.filter((e) => e.date === dateStr);
  };

  const renderCalendar = () => {
    const daysInMonth = getDaysInMonth();
    const firstDay = getFirstDayOfMonth();
    const days = [];

    // Empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      days.push(
        <div key={`empty-${i}`} className="min-h-32 border border-slate-200"></div>
      );
    }

    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const dayEvents = getEventsForDate(day);
      const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
      const isWeekend = date.getDay() === 0 || date.getDay() === 6;

      days.push(
        <div
          key={day}
          data-testid={`calendar-day-${day}`}
          className={`min-h-32 border border-slate-200 p-2 ${
            isWeekend ? "bg-slate-50" : "bg-white"
          } hover:bg-slate-50 transition-colors`}
        >
          <div className="font-medium text-slate-900 mb-2">{day}</div>
          <div className="space-y-1">
            {dayEvents.map((event, idx) => (
              <div
                key={idx}
                data-testid={`calendar-event-${event.leave_id || idx}`}
                className={`text-xs p-1.5 rounded ${
                  event.is_holiday
                    ? "bg-amber-100 text-amber-900"
                    : event.leave_type === "ooo"
                    ? "bg-red-100 text-red-900"
                    : "bg-blue-100 text-blue-900"
                } group relative`}
              >
                <div className="flex items-center justify-between">
                  <span className="truncate">
                    {event.is_holiday ? event.holiday_name : event.employee_name}
                  </span>
                  {user.role === "hr" && !event.is_holiday && (
                    <button
                      data-testid={`delete-leave-${event.leave_id}`}
                      onClick={() => handleDeleteLeave(event.leave_id)}
                      className="ml-1 opacity-0 group-hover:opacity-100 text-xs font-bold hover:scale-110 transition-all"
                    >
                      ×
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    return days;
  };

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-4xl font-bold text-slate-900">Organization Calendar</h1>
          <div className="flex items-center gap-4">
            <Button
              data-testid="prev-month-button"
              onClick={previousMonth}
              variant="outline"
              size="icon"
              className="rounded-full"
            >
              <ChevronLeft className="w-5 h-5" />
            </Button>
            <div className="text-xl font-medium text-slate-900 min-w-48 text-center">
              {MONTHS[currentDate.getMonth()]} {currentDate.getFullYear()}
            </div>
            <Button
              data-testid="next-month-button"
              onClick={nextMonth}
              variant="outline"
              size="icon"
              className="rounded-full"
            >
              <ChevronRight className="w-5 h-5" />
            </Button>
          </div>
        </div>

        {/* Legend */}
        <Card className="p-4 border border-slate-200 shadow-sm bg-white rounded-xl">
          <div className="flex gap-6 flex-wrap">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-100 border border-red-200 rounded"></div>
              <span className="text-sm text-slate-700">Out of Office</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-100 border border-blue-200 rounded"></div>
              <span className="text-sm text-slate-700">Work From Home</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-amber-100 border border-amber-200 rounded"></div>
              <span className="text-sm text-slate-700">Holiday</span>
            </div>
          </div>
        </Card>

        {/* Calendar Grid */}
        <Card className="p-6 border border-slate-200 shadow-sm bg-white rounded-xl">
          {loading ? (
            <div className="flex items-center justify-center h-96">
              <div className="text-slate-600">Loading calendar...</div>
            </div>
          ) : (
            <div className="calendar-container">
              {/* Weekday headers */}
              <div className="grid grid-cols-7 gap-0 mb-2">
                {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
                  <div
                    key={day}
                    className="text-center font-medium text-slate-700 py-2"
                  >
                    {day}
                  </div>
                ))}
              </div>
              {/* Calendar days */}
              <div className="grid grid-cols-7 gap-0 border-t border-l border-slate-200">
                {renderCalendar()}
              </div>
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
}
