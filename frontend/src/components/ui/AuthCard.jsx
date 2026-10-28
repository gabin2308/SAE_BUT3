
// Carte blanche arrondie utilisée par les 8 écrans du storyboard.
export default function AuthCard({ children, className = "" }) {
  return (
    <div
      className={`rounded-2xl bg-white p-6 shadow-lg shadow-blue-900/5 sm:p-8 ${className}`}
    >
      {children}
    </div>
  );
}