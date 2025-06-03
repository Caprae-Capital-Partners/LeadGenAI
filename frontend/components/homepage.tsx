import { useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export function HomepageContent() {
  useEffect(() => {
    // Remove any existing form to prevent duplicates
    const existing = document.querySelector('script[src*="activehosted.com/f/embed.php"]');
    if (!existing) {
      const script = document.createElement("script");
      script.src = "https://capraecapital.activehosted.com/f/embed.php?id=1";
      script.charset = "utf-8";
      script.async = true;
      document.body.appendChild(script);

      // Add custom styles for the form
      const style = document.createElement('style');
      style.textContent = `
        #_form_1_ {
          background: transparent !important;
          border: none !important;
          padding: 0 !important;
          margin: 0 !important;
        }
        #_form_1_ ._form-title {
          font-size: 1.5rem !important;
          font-weight: 600 !important;
          color: #fff !important;
          margin-bottom: 1rem !important;
        }
        #_form_1_ input[type="text"] {
          background: #1a1f2e !important;
          border: 1px solid #2d3748 !important;
          color: #fff !important;
          padding: 0.75rem 1rem !important;
          border-radius: 0.5rem !important;
          transition: all 0.2s !important;
        }
        #_form_1_ input[type="text"]:focus {
          border-color: #4fd1c5 !important;
          box-shadow: 0 0 0 2px rgba(79, 209, 197, 0.2) !important;
        }
        #_form_1_ ._submit {
          background: linear-gradient(135deg, #4fd1c5 0%, #38b2ac 100%) !important;
          border: none !important;
          padding: 0.75rem 1.5rem !important;
          border-radius: 0.5rem !important;
          font-weight: 600 !important;
          transition: all 0.2s !important;
          width: 100% !important;
          margin-top: 1rem !important;
        }
        #_form_1_ ._submit:hover {
          transform: translateY(-1px) !important;
          box-shadow: 0 4px 12px rgba(79, 209, 197, 0.2) !important;
        }
        #_form_1_ label {
          color: #e2e8f0 !important;
          font-weight: 500 !important;
          margin-bottom: 0.5rem !important;
        }
      `;
      document.head.appendChild(style);
    }
    return () => {
      const form = document.querySelector("._form_1");
      if (form) form.innerHTML = "";
    };
  }, []);

  return (
    <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 px-4">
      <div className="space-y-8 flex flex-col justify-center">
        <div className="space-y-6">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-teal-400 to-teal-600 bg-clip-text text-transparent">
            Welcome to SquatchLeads
          </h1>
          <p className="text-xl text-gray-300">
            Unlock high-quality B2B leads and accelerate your outreach with AI-powered lead generation.
          </p>
        </div>
        
        <Card className="bg-[#1a1f2e]/50 backdrop-blur-sm border-gray-800 shadow-2xl">
          <CardContent className="p-8">
            <ul className="space-y-8">
              <li className="flex items-start">
                <div className="flex-shrink-0 bg-teal-500/10 p-3 rounded-xl mr-4">
                  <svg className="h-6 w-6 text-teal-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 17l4 4 4-4m0-5V3m-8 9a9 9 0 1118 0 9 9 0 01-18 0z" />
                  </svg>
                </div>
                <div>
                  <span className="font-semibold text-gray-100 text-lg">Scraping Leads</span>
                  <p className="text-gray-400 mt-1">
                    Instantly gather targeted company and contact data from public sources.
                  </p>
                </div>
              </li>
              <li className="flex items-start">
                <div className="flex-shrink-0 bg-teal-500/10 p-3 rounded-xl mr-4">
                  <svg className="h-6 w-6 text-teal-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 1.343-3 3 0 1.657 1.343 3 3 3s3-1.343 3-3c0-1.657-1.343-3-3-3zm0 0V4m0 7v7m-7-7h14" />
                  </svg>
                </div>
                <div>
                  <span className="font-semibold text-gray-100 text-lg">Enrichment for Lead Details</span>
                  <p className="text-gray-400 mt-1">
                    Get enriched profiles: emails, phones, LinkedIn, industry, revenue, and more.
                  </p>
                </div>
              </li>
              <li className="flex items-start">
                <div className="flex-shrink-0 bg-teal-500/10 p-3 rounded-xl mr-4">
                  <svg className="h-6 w-6 text-teal-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <span className="font-semibold text-gray-100 text-lg">Save &amp; Export Leads</span>
                  <p className="text-gray-400 mt-1">
                    Save your leads to your dashboard and export to CSV or Excel for your workflow.
                  </p>
                </div>
              </li>
              <li className="flex items-start">
                <div className="flex-shrink-0 bg-teal-500/10 p-3 rounded-xl mr-4">
                  <svg className="h-6 w-6 text-teal-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                </div>
                <div>
                  <span className="font-semibold text-gray-100 text-lg">Enterprise Outreach Tools</span>
                  <p className="text-gray-400 mt-1">
                    Cold call or email directly from the platform (for enterprise members).
                  </p>
                </div>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Registration Form Section */}
      <div className="flex flex-col justify-center">
        <Card className="bg-[#1a1f2e]/80 backdrop-blur-sm border-gray-800 shadow-2xl hover:shadow-teal-500/5 transition-all duration-300">
          <CardContent className="p-8">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-white mb-2">Get Early Access</h2>
              <p className="text-gray-400">
                Join the waitlist and be the first to experience our powerful B2B lead generation platform.
              </p>
            </div>
            
            <div className="_form_1"></div>
            
            <div className="mt-6 flex items-center space-x-3 text-sm text-gray-400">
              <svg className="h-5 w-5 text-teal-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span>Your information is secure and will never be shared.</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}