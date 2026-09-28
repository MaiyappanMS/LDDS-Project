export const Table = ({ children, className = '' }) => (
  <div className={`overflow-x-auto ${className}`}><table className="w-full text-left text-sm">{children}</table></div>
);
export const Th = ({ children, className = '' }) => <th scope="col" className={`border-b border-line px-3 py-2 font-medium text-muted ${className}`}>{children}</th>;
export const Td = ({ children, className = '' }) => <td className={`border-b border-line/60 px-3 py-3 align-top ${className}`}>{children}</td>;
