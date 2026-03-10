import { useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { ArrowLeft, Mail } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/auth/forgot-password`, { email });
      setSubmitted(true);
      toast.success("If your email exists, you'll receive a reset link.");
    } catch (error) {
      toast.error("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
        <div className="w-full max-w-md fade-in">
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-slate-200 text-center">
            <div className="w-16 h-16 bg-teal-50 rounded-full flex items-center justify-center mx-auto mb-6">
              <Mail className="w-8 h-8 text-primary" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 mb-3">Check your email</h1>
            <p className="text-slate-600 mb-6">
              We've sent a password reset link to <strong>{email}</strong>
            </p>
            <p className="text-sm text-slate-500 mb-6">
              Didn't receive the email? Check your spam folder or try again.
            </p>
            <div className="space-y-3">
              <Button
                onClick={() => setSubmitted(false)}
                variant="outline"
                className="w-full h-12"
                data-testid="try-again-button"
              >
                Try another email
              </Button>
              <Link to="/">
                <Button
                  variant="ghost"
                  className="w-full h-12 text-primary"
                  data-testid="back-to-login-button"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to login
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="w-full max-w-md fade-in">
        <div className="bg-white rounded-2xl shadow-lg p-8 border border-slate-200">
          <div className="flex flex-col items-center mb-8">
            <img
              src="https://customer-assets.emergentagent.com/job_ooo-calendar-hub/artifacts/71fc0etu_Horizontal_Logo-_tortoise_%283%29_%281%29.png"
              alt="Tortoise Logo"
              className="h-12 mb-4"
            />
            <h1 className="text-2xl font-bold text-slate-900">Forgot Password?</h1>
            <p className="text-slate-600 mt-2 text-center">
              No worries! Enter your email and we'll send you a reset link.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-700">
                Work Email
              </Label>
              <Input
                id="email"
                data-testid="forgot-email-input"
                type="email"
                placeholder="your.email@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-slate-50 focus:bg-white h-12 border-slate-200"
              />
            </div>

            <Button
              type="submit"
              data-testid="forgot-submit-button"
              disabled={loading}
              className="w-full h-12 btn-pill bg-primary hover:bg-primary/90 text-white"
            >
              {loading ? "Sending..." : "Send Reset Link"}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <Link
              to="/"
              className="text-sm text-primary hover:text-primary/80 hover:underline inline-flex items-center"
              data-testid="back-to-login-link"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              Back to login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
