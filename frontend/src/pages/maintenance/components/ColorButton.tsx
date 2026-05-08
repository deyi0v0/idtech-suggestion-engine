

export default function ColorButton({ children, className, color, onClick, disabled }: { children: React.ReactNode; className?: string; color: string; onClick: () => void; disabled?: boolean }) {
    return (
        <button
            onClick={disabled ? undefined : onClick}
            disabled={disabled}
            className={[
                className ?? "",
                `bg-[${color}] text-white font-bold py-2 px-4 rounded-2xl`,
                disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer",
            ].join(" ")}
        >
            {children}
        </button>
    );
}