interface GenericButtonProps {
    onClick?: () => void;
    children?: React.ReactNode;
    className?: string;
    disabled?: boolean;
}

export default function GenericButton({
    onClick,
    children,
    className = "bg-green-700 hover:bg-green-600 text-gray-100",
    disabled = false,
}: GenericButtonProps) {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={`hover:cursor-pointer rounded-xl px-4 py-2 ${className} ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
        >
            {children ?? "Button"}
        </button>
    );
}