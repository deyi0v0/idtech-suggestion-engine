interface GenericButtonProps {
    onClick?: () => void
}

export default function GenericButton({onClick}: GenericButtonProps) {
    return (
        <button onClick={onClick} className="bg-green-700 hover:bg-green-600 hover:cursor-pointer text-gray-100 rounded-xl px-4 py-2">
            This is some text for a button
        </button>
    );
};