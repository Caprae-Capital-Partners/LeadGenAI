import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CheckCircle } from "lucide-react";

function CustomWaitlistForm() {
  const [form, setForm] = useState({ fullname: "", email: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);

    const formData = new FormData();
    formData.append("u", "1");
    formData.append("f", "1");
    formData.append("s", "");
    formData.append("c", "0");
    formData.append("m", "0");
    formData.append("act", "sub");
    formData.append("v", "2");
    formData.append("or", "fc298f4210f79b67d2157e3fc84cc565");
    formData.append("fullname", form.fullname);
    formData.append("email", form.email);

    try {
      await fetch("https://capraecapital.activehosted.com/proc.php", {
        method: "POST",
        body: formData,
        mode: "no-cors",
      });
      setIsSuccess(true);
      setForm({ fullname: "", email: "" });
    } catch (err) {
      alert("Submission failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form
        onSubmit={handleSubmit}
        className="bg-[#181c29] rounded-2xl shadow-2xl p-8 w-full border border-[#232a3d] backdrop-blur-sm"
        autoComplete="off"
    >
      <h2 className="text-2xl font-bold text-teal-400 mb-2">Get Early Access</h2>
      <p className="text-gray-300 mb-6">
        Join the waitlist and be the first to experience our powerful B2B lead generation platform.
      </p>
      {isSuccess ? (
        <div className="flex items-center text-teal-400 font-semibold text-lg py-8 justify-center">
          <CheckCircle className="mr-2" /> Thank you! You’re on the waitlist.
        </div>
      ) : (
        <>
          <div className="mb-4">
            <Label htmlFor="fullname" className="text-gray-200 mb-1 block">
              Full Name
            </Label>
            <Input
              id="fullname"
              name="fullname"
              type="text"
              required
              value={form.fullname}
              onChange={handleChange}
              className="!text-teal-300 bg-[#1A2438] border border-teal-700 focus:border-teal-400 focus:ring-2 focus:ring-teal-500/30 placeholder-gray-500 rounded-lg px-4 py-3 transition-all"
              placeholder="Type your name"
            />
          </div>
          <div className="mb-4">
            <Label htmlFor="email" className="text-gray-200 mb-1 block">
              Email <span className="text-yellow-400">*</span>
            </Label>
            <Input
              id="email"
              name="email"
              type="email"
              required
              value={form.email}
              onChange={handleChange}
              className="bg-[#1A2438] border border-teal-700 focus:border-teal-400 focus:ring-2 focus:ring-teal-500/30 !text-teal-300 placeholder-gray-500 rounded-lg px-4 py-3 transition-all"
              placeholder="Type your email"
            />
          </div>
          <Button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 rounded-lg font-bold text-lg bg-gradient-to-r from-teal-400 to-teal-600 hover:from-yellow-400 hover:to-yellow-500 text-black shadow-lg transition-all"
          >
            {isSubmitting ? "Submitting..." : "Join Waitlist"}
          </Button>
        </>
      )}
      <div className="mt-6 flex items-center space-x-3 text-sm text-gray-400">
        <svg className="h-5 w-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <span>Your information is secure and will never be shared.</span>
      </div>
    </form>
  );
}

export default CustomWaitlistForm;