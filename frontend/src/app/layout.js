import "./globals.css";

export const metadata = {
  title: "BRACU Advisor",
  description: "Ask about admissions, academics, scholarships, and more at BRAC University.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col bg-slate-50">{children}</body>
    </html>
  );
}
