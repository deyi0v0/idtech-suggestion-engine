

export default function ColorButton({ children, className, color, onClick }: { children: React.ReactNode; className?: string; color: string; onClick: () => void }) {
    return (
        <button 
            onClick={onClick}
            className={className ? className + ` bg-[${color}] text-white font-bold py-2 px-4 rounded-2xl` : ` bg-[${color}] text-white font-bold py-2 px-4 rounded-2xl`}>
            {children}
        </button>
    );
}